"""Convert run/trajectory-correlated OTel spans into a Harbor ATIF v1.7 document.

The whole point of this converter: it groups spans **purely by the
``gen_ai.session.id`` / ``gen_ai.trajectory.id`` / ``gen_ai.trajectory.parent.id``
attributes**. It never reads ``trace_id`` or ``parent_span_id``. So it
reconstructs one ATIF run even though the spans were emitted across *several
traces* with no parent-child link between them.

  run                 <- gen_ai.session.id           (the workflow span's id)
  trajectory          <- gen_ai.trajectory.id        (an agent span's id)
  sub-agent nesting   <- gen_ai.trajectory.parent.id (the invoking agent's id)
  llm/tool ownership  <- gen_ai.trajectory.id on the chat/execute_tool span

Usage:
    python3 otel_to_atif.py captured-otel-spans.json trajectory.atif.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

GAP = "CANT_POPULATE"

SESSION = "gen_ai.session.id"
TRAJECTORY = "gen_ai.trajectory.id"
PARENT_TRAJECTORY = "gen_ai.trajectory.parent.id"
OP = "gen_ai.operation.name"


def a(span, key, default=None):
    return span["attributes"].get(key, default)


def jload(span, key):
    v = a(span, key)
    return json.loads(v) if isinstance(v, str) else None


def parts_to_message(parts):
    """Split semconv message parts into (text, tool_calls)."""
    text, tool_calls = [], []
    for p in parts or []:
        t = p.get("type")
        if t == "text":
            text.append(p.get("content", ""))
        elif t == "tool_call":
            tool_calls.append(
                {
                    "tool_call_id": p.get("id"),
                    "function_name": p.get("name"),
                    "arguments": p.get("arguments", {}),
                }
            )
    return "\n".join(text), tool_calls


def metrics_from_chat(span):
    m = {}
    if a(span, "gen_ai.usage.input_tokens") is not None:
        m["prompt_tokens"] = a(span, "gen_ai.usage.input_tokens")
    if a(span, "gen_ai.usage.output_tokens") is not None:
        m["completion_tokens"] = a(span, "gen_ai.usage.output_tokens")
    return m


def build_trajectory(traj_id, agents, owned, parent_of, session_id):
    """Build one ATIF trajectory (recursively embedding its sub-agents)."""
    agent_span = agents[traj_id]
    chats = sorted(
        (s for s in owned.get(traj_id, []) if a(s, OP) == "chat"),
        key=lambda s: s["start_time_unix_nano"],
    )

    steps = []
    sid = 0

    def nid():
        nonlocal sid
        sid += 1
        return sid

    # system / user steps from the first chat's input messages
    if chats:
        for m in jload(chats[0], "gen_ai.input.messages") or []:
            role = m.get("role")
            text, _ = parts_to_message(m.get("parts"))
            if role == "system":
                steps.append(
                    {"step_id": nid(), "source": "system", "message": text}
                )
            elif role in ("user", "human"):
                steps.append(
                    {"step_id": nid(), "source": "user", "message": text}
                )

    # one agent step per chat (its assistant output)
    for chat in chats:
        outputs = jload(chat, "gen_ai.output.messages") or []
        out = outputs[0] if outputs else {"parts": []}
        message, tool_calls = parts_to_message(out.get("parts"))
        step = {
            "step_id": nid(),
            "source": "agent",
            "model_name": a(chat, "gen_ai.request.model", GAP),
            "message": message,
            "metrics": metrics_from_chat(chat),
            "llm_call_count": 1,
        }
        if tool_calls:
            step["tool_calls"] = tool_calls
        steps.append(step)

    # sub-agents: dispatch step (deterministic, no inference) + embedded trajectory
    children = sorted(
        (t for t in agents if parent_of.get(t) == traj_id),
        key=lambda t: agents[t]["start_time_unix_nano"],
    )
    for child in children:
        steps.append(
            {
                "step_id": nid(),
                "source": "agent",
                "llm_call_count": 0,
                "message": f"Delegating to {a(agents[child], 'gen_ai.agent.name', child)}.",
                "observation": {
                    "results": [
                        {"subagent_trajectory_ref": [{"trajectory_id": child}]}
                    ]
                },
            }
        )

    total_prompt = sum(
        a(c, "gen_ai.usage.input_tokens", 0) or 0 for c in chats
    )
    total_completion = sum(
        a(c, "gen_ai.usage.output_tokens", 0) or 0 for c in chats
    )

    agent_obj = {"name": a(agent_span, "gen_ai.agent.name", GAP)}
    if a(agent_span, "gen_ai.agent.description"):
        agent_obj["extra"] = {
            "description": a(agent_span, "gen_ai.agent.description")
        }

    trajectory = {
        "schema_version": "ATIF-v1.7",
        "trajectory_id": traj_id,
        "session_id": session_id,
        "agent": agent_obj,
        "steps": steps,
        "final_metrics": {
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_steps": len(steps),
        },
    }
    if a(agent_span, "gen_ai.conversation.id"):
        trajectory["extra"] = {
            "gen_ai.conversation.id": a(agent_span, "gen_ai.conversation.id")
        }
    sub = [
        build_trajectory(child, agents, owned, parent_of, session_id)
        for child in children
    ]
    if sub:
        trajectory["subagent_trajectories"] = sub
    return trajectory


def convert(path):
    spans = json.load(open(path))["spans"]

    # --- group purely by attributes; trace_id / parent_span_id are ignored ---
    agents = {}  # trajectory_id -> invoke_agent span
    owned = {}  # trajectory_id -> [chat/tool spans]
    parent_of = {}  # trajectory_id -> parent trajectory_id (or None)
    sessions = set()

    for s in spans:
        op = a(s, OP)
        sid = a(s, SESSION)
        if sid:
            sessions.add(sid)
        if op == "invoke_agent":
            tid = a(s, TRAJECTORY)
            agents[tid] = s
            parent_of[tid] = a(s, PARENT_TRAJECTORY)
        elif op in ("chat", "execute_tool"):
            tid = a(s, TRAJECTORY)
            owned.setdefault(tid, []).append(s)

    if len(sessions) != 1:
        raise SystemExit(f"expected exactly one run, found {sessions!r}")
    session_id = next(iter(sessions))

    # roots = trajectories whose parent isn't another captured trajectory
    roots = sorted(
        (t for t in agents if parent_of.get(t) not in agents),
        key=lambda t: agents[t]["start_time_unix_nano"],
    )

    trajectories = [
        build_trajectory(t, agents, owned, parent_of, session_id)
        for t in roots
    ]

    traces = {s["trace_id"] for s in spans}
    root = trajectories[0] if len(trajectories) == 1 else {
        "schema_version": "ATIF-v1.7",
        "session_id": session_id,
        "trajectories": trajectories,
    }
    root["notes"] = (
        f"Reconstructed from {len(spans)} spans across {len(traces)} traces "
        f"by gen_ai.session.id / gen_ai.trajectory.id alone; the OTel span tree "
        f"(trace_id, parent_span_id) was not used."
    )
    return root


if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else "captured-otel-spans.json"
    outp = sys.argv[2] if len(sys.argv) > 2 else "trajectory.atif.json"
    doc = convert(inp)
    Path(outp).write_text(json.dumps(doc, indent=2))
    print(f"wrote {outp}")
