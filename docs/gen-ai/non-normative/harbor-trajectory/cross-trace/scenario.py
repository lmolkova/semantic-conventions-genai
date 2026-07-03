"""Multi-agent LangGraph scenario that emits run/trajectory-correlated OTel spans.

Five agents, two levels of nesting, deliberately split across **two traces**:

    research-pipeline                         (invoke_workflow  -> session id)
      orchestrator                            (invoke_agent     -> trajectory)
        chat                                  (plans the work)
        researcher                            (invoke_agent     -> trajectory)
          chat
        writer                                (invoke_agent     -> trajectory)
          chat
    --- second trace (a "resumed" review phase, same run) ---------------------
    reviewer                                  (invoke_agent     -> trajectory)
      chat
      fact-checker                            (invoke_agent     -> trajectory)
        chat

The run (ATIF ``session_id``) is the workflow span's ``{trace}-{span}`` id; each
trajectory (ATIF ``trajectory_id``) is an agent span's ``{trace}-{span}`` id. The
instrumentation stamps both on every span via the LangChain run_id graph -- never
via the OTel span tree. The review phase runs in a *separate* ``graph.invoke``
(its own trace), so parent-child nesting cannot link it to the run; the
application carries the session id and the parent trajectory id forward as plain
data (config ``metadata``), exactly as a durable/resumed run would.

Run with the instrumentation's editable install, e.g.:

    .tox/py312-test-instrumentation-genai-langchain-conformance/bin/python scenario.py

It needs no network and no API key (a local fake OpenAI server returns canned
completions) and writes ``captured-otel-spans.json`` next to this file.
"""

from __future__ import annotations

import json
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# Capture message content on spans so the ATIF conversion has inputs/outputs.
os.environ.setdefault(
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "SPAN_ONLY"
)
# Opt in to the experimental run/trajectory correlation attributes.
os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_EMIT_RUN_CORRELATION", "true")

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph

from opentelemetry import trace
from opentelemetry.instrumentation.genai.langchain import LangChainInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

HERE = Path(__file__).resolve().parent
CONVERSATION_ID = "conv-demo-rooftop-solar"

# --------------------------------------------------------------------------- #
# Fake OpenAI server: returns a canned completion per agent (keyed by a marker
# embedded in the system prompt). Deterministic, offline, no API key.
# --------------------------------------------------------------------------- #
CANNED = {
    "orchestrator": "Plan: (1) research rooftop-solar benefits, (2) draft a 1-sentence brief, (3) review it.",
    "researcher": "Rooftop solar cuts a household's electricity bill by roughly half and tends to raise resale value.",
    "writer": "Rooftop solar pays homeowners twice: about 50% lower power bills and a higher resale price.",
    "reviewer": "The draft is clear and accurate; the ~50% savings figure should be verified.",
    "fact-checker": "Verified: a ~50% bill reduction is well supported for typical residential installs.",
}
_MARKER = re.compile(r"\[agent:([^\]]+)\]")


class _FakeOpenAI(BaseHTTPRequestHandler):
    def log_message(self, *_a):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        agent = "orchestrator"
        for msg in payload.get("messages", []):
            content = msg.get("content")
            if isinstance(content, str):
                found = _MARKER.search(content)
                if found:
                    agent = found.group(1)
                    break
        content = CANNED.get(agent, "OK.")
        body = {
            "id": f"chatcmpl-{agent}",
            "object": "chat.completion",
            "created": 0,
            "model": payload.get("model", "gpt-4o-mini"),
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 40,
                "completion_tokens": 20,
                "total_tokens": 60,
            },
        }
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _start_fake_openai() -> str:
    server = HTTPServer(("127.0.0.1", 0), _FakeOpenAI)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_address[1]}/v1"


# --------------------------------------------------------------------------- #
# Agent plumbing
# --------------------------------------------------------------------------- #
def current_span_id() -> str | None:
    """The active span's ``{trace}-{span}`` id -- what the instrumentation uses
    as the run/trajectory id. The application can read it for free to persist
    and carry into a later, separate-trace segment of the same run."""
    ctx = trace.get_current_span().get_span_context()
    if not ctx.is_valid:
        return None
    return f"{ctx.trace_id:032x}-{ctx.span_id:016x}"


def call_agent(runnable, text, parent_config, name, **extra_meta):
    """Invoke a sub-agent runnable, linking it into the LangChain run_id graph
    (via the parent's callbacks) while giving it its OWN agent metadata."""
    meta = {
        "agent_name": name,
        "otel_agent_span": True,
        "conversation_id": CONVERSATION_ID,
        **extra_meta,
    }
    cfg = {
        "callbacks": (parent_config or {}).get("callbacks"),
        "metadata": meta,
    }
    return runnable.invoke(text, cfg)


def make_llm(base_url: str) -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o-mini",
        api_key="test",
        base_url=base_url,
        temperature=0.0,
        max_retries=0,
    )


def build_agents(llm: ChatOpenAI, captured: dict):
    def researcher_fn(text, config=None):
        resp = llm.invoke(
            [
                SystemMessage(
                    content="[agent:researcher] You gather factual background."
                ),
                HumanMessage(content=text),
            ],
            config,
        )
        return resp.content

    def writer_fn(text, config=None):
        resp = llm.invoke(
            [
                SystemMessage(
                    content="[agent:writer] You turn findings into a 1-sentence brief."
                ),
                HumanMessage(content=text),
            ],
            config,
        )
        return resp.content

    def fact_checker_fn(text, config=None):
        resp = llm.invoke(
            [
                SystemMessage(
                    content="[agent:fact-checker] You verify factual claims."
                ),
                HumanMessage(content=text),
            ],
            config,
        )
        return resp.content

    researcher = RunnableLambda(researcher_fn, name="researcher")
    writer = RunnableLambda(writer_fn, name="writer")
    fact_checker = RunnableLambda(fact_checker_fn, name="fact-checker")

    def orchestrator_fn(task, config=None):
        # Inside the orchestrator agent span: the app can read its trajectory id
        # for free, to carry into the separate-trace review phase.
        captured["orchestrator_trajectory"] = current_span_id()
        llm.invoke(
            [
                SystemMessage(
                    content="[agent:orchestrator] You plan and delegate."
                ),
                HumanMessage(content=task),
            ],
            config,
        )
        research = call_agent(researcher, task, config, "researcher")
        draft = call_agent(writer, research, config, "writer")
        return draft

    def reviewer_fn(draft, config=None):
        review = llm.invoke(
            [
                SystemMessage(
                    content="[agent:reviewer] You review the draft for accuracy."
                ),
                HumanMessage(content=draft),
            ],
            config,
        )
        # fact-checker nests under reviewer via the run_id graph (same trace).
        return call_agent(fact_checker, review.content, config, "fact-checker")

    orchestrator = RunnableLambda(orchestrator_fn, name="orchestrator")
    reviewer = RunnableLambda(reviewer_fn, name="reviewer")
    return orchestrator, reviewer


def build_workflow(orchestrator, captured: dict):
    def orchestrate_node(state: MessagesState, config=None):
        # Inside the workflow span: read the run (session) id for free.
        captured["session_id"] = current_span_id()
        task = state["messages"][-1].content
        draft = call_agent(orchestrator, task, config, "orchestrator")
        return {"messages": [AIMessage(content=draft)]}

    builder = StateGraph(MessagesState)
    builder.add_node("orchestrate", orchestrate_node)
    builder.add_edge(START, "orchestrate")
    builder.add_edge("orchestrate", END)
    return builder.compile()


# --------------------------------------------------------------------------- #
# Span -> dict (the JSON the converter consumes)
# --------------------------------------------------------------------------- #
def span_to_dict(span) -> dict:
    ctx = span.context
    parent = span.parent
    return {
        "name": span.name,
        "kind": span.kind.name,
        "trace_id": f"{ctx.trace_id:032x}",
        "span_id": f"{ctx.span_id:016x}",
        "parent_span_id": f"{parent.span_id:016x}" if parent else None,
        "start_time_unix_nano": span.start_time,
        "end_time_unix_nano": span.end_time,
        "attributes": dict(span.attributes or {}),
    }


def main():
    base_url = _start_fake_openai()

    exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

    llm = make_llm(base_url)
    captured: dict = {}
    orchestrator, reviewer = build_agents(llm, captured)
    workflow_graph = build_workflow(orchestrator, captured)

    task = "Write a 1-sentence brief on the benefits of rooftop solar for homeowners."

    # ---- Trace 1: the workflow (orchestrator -> researcher, writer) --------- #
    result = workflow_graph.invoke(
        {"messages": [HumanMessage(content=task)]},
        config={
            "metadata": {
                "otel_workflow_span": True,
                "workflow_name": "research-pipeline",
                "conversation_id": CONVERSATION_ID,
            }
        },
    )
    draft = result["messages"][-1].content

    session_id = captured["session_id"]
    orchestrator_trajectory = captured["orchestrator_trajectory"]
    print(f"run (session) id:        {session_id}")
    print(f"orchestrator trajectory: {orchestrator_trajectory}")

    # ---- Trace 2: a separate invoke -- the "resumed" review phase ----------- #
    # No shared OTel context with trace 1. The application carries the run id and
    # the parent trajectory forward as plain data, so the spans still join the run.
    reviewer.invoke(
        draft,
        {
            "metadata": {
                "agent_name": "reviewer",
                "otel_agent_span": True,
                "conversation_id": CONVERSATION_ID,
                "otel_session_id": session_id,
                "otel_parent_trajectory_id": orchestrator_trajectory,
            }
        },
    )

    LangChainInstrumentor().uninstrument()
    tracer_provider.force_flush()

    spans = [span_to_dict(s) for s in exporter.get_finished_spans()]
    out = HERE / "captured-otel-spans.json"
    out.write_text(json.dumps({"spans": spans}, indent=2))

    traces = {s["trace_id"] for s in spans}
    print(f"\ncaptured {len(spans)} spans across {len(traces)} traces -> {out.name}")
    for s in spans:
        a = s["attributes"]
        print(
            f"  {s['name']:<26} op={a.get('gen_ai.operation.name'):<16} "
            f"trace={s['trace_id'][:8]} "
            f"sess={(a.get('gen_ai.session.id') or '-')[-17:]} "
            f"traj={(a.get('gen_ai.trajectory.id') or '-')[-17:]} "
            f"parent={(a.get('gen_ai.trajectory.parent.id') or '-')[-17:]}"
        )


if __name__ == "__main__":
    main()
