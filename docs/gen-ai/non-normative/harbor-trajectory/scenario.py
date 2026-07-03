"""Self-contained multi-agent + orchestrator reference scenario.

Emits real OpenTelemetry spans following the GenAI semantic conventions in this
repo (gen_ai.* attributes, message JSON shapes, span names) for a workflow that
orchestrates two sub-agents and a tool. Spans are exported to a JSON file via an
in-memory exporter so the actual telemetry can be converted to a Harbor ATIF
trajectory.

Topology (span tree):

  invoke_workflow research-assistant            (orchestrator)
    plan research-assistant                     (task decomposition)
    invoke_agent researcher                     (internal sub-agent)
      chat gpt-4o-mini                          (inference -> tool call)
      execute_tool web_search                   (tool)
      chat gpt-4o-mini                          (inference -> findings)
    invoke_agent writer                         (internal sub-agent)
      chat gpt-4o-mini                          (inference -> final brief, with reasoning)
"""

import json
import sys

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

exporter = InMemorySpanExporter()
tp = TracerProvider(resource=Resource.get_empty())
tp.add_span_processor(SimpleSpanProcessor(exporter))
trace.set_tracer_provider(tp)
tracer = trace.get_tracer("gen_ai.reference")

MODEL = "gpt-4o-mini"
PROVIDER = "openai"
SERVER = ("api.openai.com", 443)
CONVERSATION_ID = "conv_demo_8a1f"

USER_TASK = "Write a 2-sentence brief on the benefits of rooftop solar for homeowners."

# Flat shape per the semconv tool-definitions JSON schema
# (FunctionToolDefinition: {type, name, description, parameters}) -- NOT the
# OpenAI-nested {"type":"function","function":{...}} shape ATIF expects.
WEB_SEARCH_DEF = {
    "type": "function",
    "name": "web_search",
    "description": "Search the web for up-to-date information.",
    "parameters": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
}


def msg(role, *parts):
    return {"role": role, "parts": list(parts)}


def text(content):
    return {"type": "text", "content": content}


def run():
    # ASSUMPTION: an invoke_workflow span driven by an agent is a special kind of
    # agent span and MAY carry the agent attributes (agent.version, agent.description,
    # and -- if the orchestrator runs inference -- request.model). See README "IDEA:
    # blend agent and workflow spans".
    wf_attrs = {
        "gen_ai.operation.name": "invoke_workflow",
        "gen_ai.workflow.name": "research-assistant",
        "gen_ai.agent.version": "0.3.0",
        "gen_ai.agent.description": "Orchestrates the researcher and writer agents.",
        "gen_ai.conversation.id": CONVERSATION_ID,
    }
    with tracer.start_as_current_span("invoke_workflow research-assistant", attributes=wf_attrs) as wf:
        wf.set_attribute("gen_ai.input.messages", json.dumps([msg("user", text(USER_TASK))]))

        # --- planning ---
        # NOTE: gen_ai.input.messages / gen_ai.output.messages are NOT yet defined
        # on the `plan` span by the conventions. We treat that as a bug and assume
        # the plan span carries them (its output == the task decomposition).
        plan_decomposition = (
            "Plan: (1) use the researcher agent to gather facts on rooftop solar benefits; "
            "(2) use the writer agent to turn the findings into a 2-sentence brief."
        )
        with tracer.start_as_current_span(
            "plan research-assistant",
            attributes={"gen_ai.operation.name": "plan", "gen_ai.agent.name": "research-assistant"},
        ) as plan_span:
            plan_span.set_attribute("gen_ai.input.messages", json.dumps([msg("user", text(USER_TASK))]))
            plan_span.set_attribute("gen_ai.output.messages", json.dumps([
                {"role": "assistant", "parts": [text(plan_decomposition)], "finish_reason": "stop"}
            ]))

        # --- researcher sub-agent ---
        researcher_instr = "You are a research assistant. Use web_search to find facts, then summarize."
        ra_attrs = {
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": "researcher",
            "gen_ai.agent.description": "Finds and summarizes facts using web search.",
            "gen_ai.agent.version": "1.2.0",
            "gen_ai.request.model": MODEL,
            "gen_ai.conversation.id": CONVERSATION_ID,
        }
        with tracer.start_as_current_span("invoke_agent researcher", attributes=ra_attrs) as ra:
            ra.set_attribute("gen_ai.system_instructions", json.dumps([text(researcher_instr)]))
            ra.set_attribute("gen_ai.input.messages", json.dumps([msg("user", text(USER_TASK))]))
            ra.set_attribute("gen_ai.tool.definitions", json.dumps([WEB_SEARCH_DEF]))

            # inference #1 -> tool call
            tool_call_part = {
                "type": "tool_call",
                "id": "call_ws_01",
                "name": "web_search",
                "arguments": {"query": "rooftop solar benefits homeowners"},
            }
            with tracer.start_as_current_span(
                "chat gpt-4o-mini",
                attributes={
                    "gen_ai.operation.name": "chat",
                    "gen_ai.provider.name": PROVIDER,
                    "gen_ai.request.model": MODEL,
                    "server.address": SERVER[0],
                    "server.port": SERVER[1],
                    "gen_ai.conversation.id": CONVERSATION_ID,
                },
            ) as c1:
                c1.set_attribute("gen_ai.system_instructions", json.dumps([text(researcher_instr)]))
                c1.set_attribute("gen_ai.input.messages", json.dumps([msg("user", text(USER_TASK))]))
                c1.set_attribute("gen_ai.tool.definitions", json.dumps([WEB_SEARCH_DEF]))
                c1.set_attribute("gen_ai.output.messages", json.dumps([
                    {"role": "assistant", "parts": [tool_call_part], "finish_reason": "tool_calls"}
                ]))
                c1.set_attribute("gen_ai.response.id", "chatcmpl-r1")
                c1.set_attribute("gen_ai.response.model", "gpt-4o-mini-2024-07-18")
                c1.set_attribute("gen_ai.response.finish_reasons", ["tool_calls"])
                c1.set_attribute("gen_ai.usage.input_tokens", 95)
                c1.set_attribute("gen_ai.usage.output_tokens", 18)

            # tool execution
            tool_result = "Rooftop solar cuts electricity bills by ~50% on average and can raise home resale value."
            with tracer.start_as_current_span(
                "execute_tool web_search",
                attributes={
                    "gen_ai.operation.name": "execute_tool",
                    "gen_ai.tool.name": "web_search",
                    "gen_ai.tool.type": "function",
                    "gen_ai.tool.description": "Search the web for up-to-date information.",
                    "gen_ai.tool.call.id": "call_ws_01",
                    "gen_ai.agent.name": "researcher",
                },
            ) as ts:
                ts.set_attribute("gen_ai.tool.call.arguments", json.dumps({"query": "rooftop solar benefits homeowners"}))
                ts.set_attribute("gen_ai.tool.call.result", json.dumps(tool_result))

            # inference #2 -> findings
            findings = "Rooftop solar typically reduces electricity bills by about half and tends to increase a home's resale value."
            with tracer.start_as_current_span(
                "chat gpt-4o-mini",
                attributes={
                    "gen_ai.operation.name": "chat",
                    "gen_ai.provider.name": PROVIDER,
                    "gen_ai.request.model": MODEL,
                    "server.address": SERVER[0],
                    "server.port": SERVER[1],
                    "gen_ai.conversation.id": CONVERSATION_ID,
                },
            ) as c2:
                c2.set_attribute("gen_ai.system_instructions", json.dumps([text(researcher_instr)]))
                c2.set_attribute("gen_ai.input.messages", json.dumps([
                    msg("user", text(USER_TASK)),
                    {"role": "assistant", "parts": [tool_call_part]},
                    {"role": "tool", "parts": [{"type": "tool_call_response", "id": "call_ws_01", "response": tool_result}]},
                ]))
                c2.set_attribute("gen_ai.output.messages", json.dumps([
                    {"role": "assistant", "parts": [text(findings)], "finish_reason": "stop"}
                ]))
                c2.set_attribute("gen_ai.response.id", "chatcmpl-r2")
                c2.set_attribute("gen_ai.response.model", "gpt-4o-mini-2024-07-18")
                c2.set_attribute("gen_ai.response.finish_reasons", ["stop"])
                c2.set_attribute("gen_ai.usage.input_tokens", 140)
                c2.set_attribute("gen_ai.usage.output_tokens", 32)

            ra.set_attribute("gen_ai.output.messages", json.dumps([
                {"role": "assistant", "parts": [text(findings)], "finish_reason": "stop"}
            ]))
            ra.set_attribute("gen_ai.usage.input_tokens", 235)
            ra.set_attribute("gen_ai.usage.output_tokens", 50)

        # --- writer sub-agent (with reasoning) ---
        writer_instr = "You are a concise technical writer. Produce a polished 2-sentence brief."
        wr_attrs = {
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": "writer",
            "gen_ai.agent.description": "Turns research findings into a polished brief.",
            "gen_ai.agent.version": "1.0.0",
            "gen_ai.request.model": MODEL,
            "gen_ai.request.reasoning.level": "medium",
            "gen_ai.conversation.id": CONVERSATION_ID,
        }
        final_brief = (
            "Rooftop solar can cut a household's electricity bills by roughly half, delivering "
            "substantial long-term savings. It also tends to raise a home's resale value, making "
            "it both an operational and an investment win for homeowners."
        )
        with tracer.start_as_current_span("invoke_agent writer", attributes=wr_attrs) as wr:
            wr.set_attribute("gen_ai.system_instructions", json.dumps([text(writer_instr)]))
            wr.set_attribute("gen_ai.input.messages", json.dumps([msg("user", text(findings))]))

            with tracer.start_as_current_span(
                "chat gpt-4o-mini",
                attributes={
                    "gen_ai.operation.name": "chat",
                    "gen_ai.provider.name": PROVIDER,
                    "gen_ai.request.model": MODEL,
                    "gen_ai.request.reasoning.level": "medium",
                    "server.address": SERVER[0],
                    "server.port": SERVER[1],
                    "gen_ai.conversation.id": CONVERSATION_ID,
                },
            ) as c3:
                c3.set_attribute("gen_ai.system_instructions", json.dumps([text(writer_instr)]))
                c3.set_attribute("gen_ai.input.messages", json.dumps([msg("user", text(findings))]))
                c3.set_attribute("gen_ai.output.messages", json.dumps([
                    {
                        "role": "assistant",
                        "parts": [
                            {"type": "reasoning", "content": "Combine the savings and resale points into two crisp sentences."},
                            text(final_brief),
                        ],
                        "finish_reason": "stop",
                    }
                ]))
                c3.set_attribute("gen_ai.response.id", "chatcmpl-w1")
                c3.set_attribute("gen_ai.response.model", "gpt-4o-mini-2024-07-18")
                c3.set_attribute("gen_ai.response.finish_reasons", ["stop"])
                c3.set_attribute("gen_ai.usage.input_tokens", 60)
                c3.set_attribute("gen_ai.usage.output_tokens", 55)
                c3.set_attribute("gen_ai.usage.reasoning.output_tokens", 12)

            wr.set_attribute("gen_ai.output.messages", json.dumps([
                {"role": "assistant", "parts": [text(final_brief)], "finish_reason": "stop"}
            ]))
            wr.set_attribute("gen_ai.usage.input_tokens", 60)
            wr.set_attribute("gen_ai.usage.output_tokens", 55)

        wf.set_attribute("gen_ai.output.messages", json.dumps([
            {"role": "assistant", "parts": [text(final_brief)], "finish_reason": "stop"}
        ]))


def serialize():
    out = []
    for s in exporter.get_finished_spans():
        ctx = s.context
        out.append({
            "name": s.name,
            "trace_id": format(ctx.trace_id, "032x"),
            "span_id": format(ctx.span_id, "016x"),
            "parent_span_id": format(s.parent.span_id, "016x") if s.parent else None,
            "kind": s.kind.name,
            "start_time_unix_nano": s.start_time,
            "end_time_unix_nano": s.end_time,
            "attributes": dict(s.attributes),
        })
    # order by start time so the tree reads top-down
    out.sort(key=lambda x: x["start_time_unix_nano"])
    return out


if __name__ == "__main__":
    run()
    tp.force_flush()
    spans = serialize()
    path = sys.argv[1] if len(sys.argv) > 1 else "captured-otel-spans.json"
    with open(path, "w") as f:
        json.dump({"spans": spans}, f, indent=2)
    print(f"wrote {len(spans)} spans to {path}")
