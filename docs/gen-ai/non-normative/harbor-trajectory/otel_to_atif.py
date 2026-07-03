"""Convert captured OTel GenAI spans (spans.json) into a Harbor ATIF v1.7 trajectory.

This is a faithful, mechanical mapping. Where the GenAI semantic conventions
provide no source for a required/optional ATIF field, the value is the sentinel
string "CANT_POPULATE" so gaps are explicit in the output.
"""

import json
import sys
from datetime import datetime, timezone

GAP = "CANT_POPULATE"
NA_CLIENT = "NOT_AVAILABLE_CLIENT_SIDE"


def load(path):
    spans = json.load(open(path))["spans"]
    by_id = {s["span_id"]: s for s in spans}
    children = {}
    for s in spans:
        children.setdefault(s["parent_span_id"], []).append(s)
    for kids in children.values():
        kids.sort(key=lambda x: x["start_time_unix_nano"])
    return spans, by_id, children


def iso(nanos):
    return datetime.fromtimestamp(nanos / 1e9, tz=timezone.utc).isoformat()


def a(span, key, default=None):
    return span["attributes"].get(key, default)


def jload(span, key):
    v = a(span, key)
    return json.loads(v) if v is not None else None


def child_spans(children, span, op):
    return [c for c in children.get(span["span_id"], []) if a(c, "gen_ai.operation.name") == op]


def metrics_from_inference(inf):
    m = {}
    if a(inf, "gen_ai.usage.input_tokens") is not None:
        m["prompt_tokens"] = a(inf, "gen_ai.usage.input_tokens")
    if a(inf, "gen_ai.usage.output_tokens") is not None:
        m["completion_tokens"] = a(inf, "gen_ai.usage.output_tokens")
    # ATIF cached_tokens <- gen_ai.usage.cache_read.input_tokens (not emitted here)
    m["cached_tokens"] = a(inf, "gen_ai.usage.cache_read.input_tokens", GAP)
    m["cost_usd"] = GAP            # no semconv attribute
    # Integer tokenizer IDs are not exposed by client APIs (only by the inference
    # server that owns the tokenizer) -- not a semconv gap, a client-side limit.
    m["prompt_token_ids"] = NA_CLIENT
    m["completion_token_ids"] = NA_CLIENT
    m["logprobs"] = GAP            # logprob values are unmodeled by semconv
    reasoning_tokens = a(inf, "gen_ai.usage.reasoning.output_tokens")
    if reasoning_tokens is not None:
        m["extra"] = {"reasoning_output_tokens": reasoning_tokens}  # no native ATIF field
    return m


def parts_to_message_and_tools(parts):
    """Split a semconv message's parts into ATIF (message, tool_calls, reasoning_content)."""
    text_chunks, tool_calls, reasoning = [], [], []
    for p in parts:
        t = p.get("type")
        if t == "text":
            text_chunks.append(p["content"])
        elif t == "reasoning":
            reasoning.append(p.get("content", ""))
        elif t == "tool_call":
            tool_calls.append({
                "tool_call_id": p["id"],
                "function_name": p["name"],
                "arguments": p.get("arguments", {}),
            })
    message = "\n".join(text_chunks) if text_chunks else ""
    return message, tool_calls, ("\n".join(reasoning) if reasoning else None)


def convert_agent(agent_span, by_id, children):
    """Build a sub-trajectory (Trajectory object) from one invoke_agent span subtree."""
    # A trajectory is scoped by ONE invoke_agent span, so its stable id is that
    # span's span_id -- NOT the trace_id (a trace can contain many trajectories,
    # and a single trajectory can span many traces).
    trajectory_id = agent_span["span_id"]
    name = a(agent_span, "gen_ai.agent.name")
    inferences = child_spans(children, agent_span, "chat")
    tool_spans = {a(t, "gen_ai.tool.call.id"): t for t in child_spans(children, agent_span, "execute_tool")}

    # tool_definitions: reshape semconv's FLAT FunctionToolDefinition
    # ({type,name,description,parameters}) into the OpenAI-nested shape ATIF
    # expects ({type:"function","function":{...}}). Mechanical, lossless.
    raw_defs = jload(agent_span, "gen_ai.tool.definitions")
    tool_defs = None
    if raw_defs is not None:
        tool_defs = []
        for d in raw_defs:
            if d.get("type") == "function" and "function" not in d:
                tool_defs.append({"type": "function", "function": {
                    k: d[k] for k in ("name", "description", "parameters") if k in d
                }})
            else:
                tool_defs.append(d)

    agent_obj = {
        "name": name,
        "version": a(agent_span, "gen_ai.agent.version", GAP),
        "model_name": a(agent_span, "gen_ai.request.model", GAP),
    }
    if tool_defs is not None:
        agent_obj["tool_definitions"] = tool_defs
    desc = a(agent_span, "gen_ai.agent.description")
    if desc:
        agent_obj["extra"] = {"description": desc}

    steps = []
    sid = 0

    def next_id():
        nonlocal sid
        sid += 1
        return sid

    # 1) system step from system_instructions
    sys_instr = jload(agent_span, "gen_ai.system_instructions")
    if sys_instr:
        sys_text = "\n".join(p.get("content", "") for p in sys_instr if p.get("type", "text") == "text")
        steps.append({"step_id": next_id(), "timestamp": iso(agent_span["start_time_unix_nano"]),
                      "source": "system", "message": sys_text})

    # 2) initial inputs (user / prior history) from the FIRST inference's input.messages
    if inferences:
        first_inputs = jload(inferences[0], "gen_ai.input.messages") or []
        for m in first_inputs:
            role = m["role"]
            if role == "user":
                msg, _, _ = parts_to_message_and_tools(m["parts"])
                steps.append({"step_id": next_id(), "timestamp": iso(inferences[0]["start_time_unix_nano"]),
                              "source": "user", "message": msg})
            # assistant/tool entries in the first input are reconstructed below from spans

    # 3) one agent step per inference (its assistant output), with observation from tools
    for inf in inferences:
        outputs = jload(inf, "gen_ai.output.messages") or []
        out = outputs[0] if outputs else {"parts": []}
        message, tool_calls, reasoning = parts_to_message_and_tools(out.get("parts", []))
        step = {
            "step_id": next_id(),
            "timestamp": iso(inf["start_time_unix_nano"]),
            "source": "agent",
            "model_name": a(inf, "gen_ai.request.model", GAP),
            "message": message,
            "metrics": metrics_from_inference(inf),
            "llm_call_count": 1,
        }
        if a(inf, "gen_ai.request.reasoning.level") is not None:
            step["reasoning_effort"] = a(inf, "gen_ai.request.reasoning.level")
        if reasoning is not None:
            step["reasoning_content"] = reasoning
        if tool_calls:
            step["tool_calls"] = tool_calls
            results = []
            for tc in tool_calls:
                ts = tool_spans.get(tc["tool_call_id"])
                content = json.loads(a(ts, "gen_ai.tool.call.result")) if ts and a(ts, "gen_ai.tool.call.result") else GAP
                results.append({"source_call_id": tc["tool_call_id"], "content": content})
            step["observation"] = {"results": results}
        steps.append(step)

    # final_metrics aggregated from agent-level usage
    final = {
        "total_prompt_tokens": a(agent_span, "gen_ai.usage.input_tokens", GAP),
        "total_completion_tokens": a(agent_span, "gen_ai.usage.output_tokens", GAP),
        "total_steps": len(steps),
        "total_cost_usd": GAP,
    }

    return {
        "schema_version": "ATIF-v1.7",
        "trajectory_id": trajectory_id,
        # session_id is the RUN -- a logical scope with no OTel equivalent. trace_id
        # is a transport construct (a run may span traces; a trace may hold runs),
        # and conversation.id is the broader thread. No attribute identifies a run.
        "session_id": GAP,
        "agent": agent_obj,
        "steps": steps,
        "final_metrics": final,
    }


def convert(path):
    spans, by_id, children = load(path)
    roots = children.get(None, [])
    wf = next((s for s in roots if a(s, "gen_ai.operation.name") == "invoke_workflow"), None)
    if wf is None:
        raise SystemExit("no invoke_workflow root span found")

    agent_children = child_spans(children, wf, "invoke_agent")
    plan_children = child_spans(children, wf, "plan")

    sub_trajectories = [convert_agent(ag, by_id, children) for ag in agent_children]

    # Root trajectory == orchestrator workflow.
    steps = []
    sid = 0

    def nid():
        nonlocal sid
        sid += 1
        return sid

    wf_in = jload(wf, "gen_ai.input.messages") or []
    for m in wf_in:
        if m["role"] == "user":
            msg, _, _ = parts_to_message_and_tools(m["parts"])
            steps.append({"step_id": nid(), "timestamp": iso(wf["start_time_unix_nano"]),
                          "source": "user", "message": msg})

    # plan step. ASSUMPTION: the plan span carries gen_ai.output.messages (the
    # task decomposition). This is not yet defined by the conventions -- see the
    # plan-gap note in README.md.
    for pl in plan_children:
        plan_out = jload(pl, "gen_ai.output.messages") or []
        plan_msg = GAP
        if plan_out:
            plan_msg, _, _ = parts_to_message_and_tools(plan_out[0].get("parts", []))
        steps.append({"step_id": nid(), "timestamp": iso(pl["start_time_unix_nano"]),
                      "source": "agent", "llm_call_count": 1,  # plan output is LLM-generated
                      "message": plan_msg,
                      "extra": {"step_type": "plan"}})

    # one deterministic dispatch step per sub-agent, linking the embedded sub-trajectory
    for ag in agent_children:
        steps.append({
            "step_id": nid(),
            "timestamp": iso(ag["start_time_unix_nano"]),
            "source": "agent",
            "llm_call_count": 0,  # orchestrator dispatch is deterministic (no LLM inference span)
            "message": GAP,       # workflow span records no per-dispatch message
            "observation": {"results": [{
                # source_call_id omitted: optional in ATIF and N/A here (a workflow
                # dispatch is a span-tree parent->child edge, not an LLM tool call).
                "subagent_trajectory_ref": [{"trajectory_id": ag["span_id"]}],
            }]},
        })

    wf_out = jload(wf, "gen_ai.output.messages") or []
    for m in wf_out:
        if m["role"] == "assistant":
            msg, _, _ = parts_to_message_and_tools(m["parts"])
            steps.append({"step_id": nid(), "timestamp": iso(wf["end_time_unix_nano"]),
                          "source": "agent", "llm_call_count": 0, "message": msg})

    root = {
        "schema_version": "ATIF-v1.7",
        # Root trajectory id = the workflow span's span_id (scopes this trajectory).
        # session_id = gen_ai.conversation.id, which groups trajectories that may
        # span multiple traces.
        "trajectory_id": wf["span_id"],
        "session_id": GAP,  # the run has no OTel identifier (see convert_agent)
        "agent": {
            "name": a(wf, "gen_ai.workflow.name", GAP),
            # Blend assumption: the workflow span may carry agent attributes.
            "version": a(wf, "gen_ai.agent.version", GAP),
            # model_name only if the orchestrator itself runs inference; ours is
            # deterministic, so it stays unset.
            "model_name": a(wf, "gen_ai.request.model", GAP),
            "extra": {
                "otel_kind": "workflow",
                "note": "ATIF has no workflow concept; mapped onto AgentSchema",
                **({"description": a(wf, "gen_ai.agent.description")} if a(wf, "gen_ai.agent.description") else {}),
            },
        },
        "steps": steps,
        "subagent_trajectories": sub_trajectories,
        # gen_ai.conversation.id is the thread/conversation -- a scope ABOVE the
        # run, with no ATIF field. Kept here for traceability.
        "extra": {"gen_ai.conversation.id": a(wf, "gen_ai.conversation.id", GAP)},
        "notes": "Orchestrator is a gen_ai invoke_workflow span; sub-agents are invoke_agent spans.",
    }
    return root


if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else "captured-otel-spans.json"
    outp = sys.argv[2] if len(sys.argv) > 2 else "sample-trajectory.atif.json"
    traj = convert(inp)
    with open(outp, "w") as f:
        json.dump(traj, f, indent=2)
    print(f"wrote trajectory to {outp}")
