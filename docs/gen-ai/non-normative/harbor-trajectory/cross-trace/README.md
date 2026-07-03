# Cross-trace runs: deriving session & trajectory ids from trace + span ids

A **runnable** companion to the parent doc's
[trace context vs trajectory id — edge cases](../README.md#context-trace-context-vs-trajectory-id--possible-edge-cases).
That section argued a run (`session_id`) and a trajectory (`trajectory_id`) are
*application-level* groupings that cross-cut `trace_id`. This folder implements
the concrete proposal from it — **give each its own id, derived from the
originating span, and carry it in attributes** — by modifying the real
[LangChain GenAI instrumentation](https://github.com/open-telemetry/opentelemetry-python-genai)
and reconstructing one ATIF run from spans emitted across **two separate traces**.

| File | What it is |
| --- | --- |
| [scenario.py](scenario.py) | 5 agents, 2 levels of nesting, run across two `graph.invoke` calls (two traces). Offline (a local fake OpenAI server); no API key. |
| [captured-otel-spans.json](captured-otel-spans.json) | The 11 spans it emitted, across 2 trace ids. |
| [otel_to_atif.py](otel_to_atif.py) | Converter that groups **only** by the new id attributes — it never reads `trace_id` or `parent_span_id`. |
| [trajectory.atif.json](trajectory.atif.json) | The single ATIF run it reconstructs from both traces. |

The instrumentation change is in the sibling repo:
[`callback_handler.py`](https://github.com/open-telemetry/opentelemetry-python-genai/blob/main/instrumentation/opentelemetry-instrumentation-genai-langchain/src/opentelemetry/instrumentation/genai/langchain/callback_handler.py).
It is **opt-in** (env var `OTEL_INSTRUMENTATION_GENAI_EMIT_RUN_CORRELATION=true`);
with it off, telemetry is unchanged.

## The shape

```
research-pipeline                       invoke_workflow   -> session id
  orchestrator                          invoke_agent      -> trajectory
    chat (plans)
    researcher                          invoke_agent      -> trajectory
      chat
    writer                              invoke_agent      -> trajectory
      chat
  ── trace boundary: a separate graph.invoke, the "review" phase ──
  reviewer                              invoke_agent      -> trajectory
    chat
    fact-checker                        invoke_agent      -> trajectory
      chat
```

`orchestrator → {researcher, writer, reviewer}` and `reviewer → fact-checker`
(two levels). The first three agents run in **trace 1**; `reviewer` and
`fact-checker` run in **trace 2** but belong to the same run.

## The three attributes

The instrumentation stamps these on every GenAI span when enabled:

| Attribute | Value | On |
| --- | --- | --- |
| `gen_ai.session.id` | `{trace_id}-{span_id}` of the **workflow** span (the run's start) | every span in the run |
| `gen_ai.trajectory.id` | `{trace_id}-{span_id}` of the **agent** span (the trajectory's start) | the agent span + its child `chat`/`execute_tool` spans |
| `gen_ai.trajectory.parent.id` | the invoking agent's `trajectory.id` | sub-agent spans (expresses nesting) |

`session.id ≈ trace+span` of where the run began; `trajectory.id ≈ trace+span`
of where the agent began. They are just strings; consumers treat them as opaque
keys.

## Run it

```bash
# Use an interpreter that has langchain-openai + langgraph + the (editable) instrumentation.
.tox/py312-test-instrumentation-genai-langchain-conformance/bin/python scenario.py
python3 otel_to_atif.py captured-otel-spans.json trajectory.atif.json
```

## How the run is reconstructed — without the span tree

[otel_to_atif.py](otel_to_atif.py) groups spans into one ATIF run **purely by the
three attributes**: agents keyed by `trajectory.id`, nested by
`trajectory.parent.id`, with `chat`/`tool` spans attached by their `trajectory.id`,
all sharing one `session.id`. It **never reads `trace_id` or `parent_span_id`**
(it touches `trace_id` only to print "…across N traces" in the notes).

That is why the run survives the trace boundary. In the captured data,
`reviewer` is a root span of trace 2 (`parent_span_id = null`), yet its
`trajectory.parent.id` points at `orchestrator` — a span in **trace 1**. The OTel
span tree *cannot* represent that edge; the attribute does. Scrambling every
`trace_id` to one value, or shuffling span order, leaves the reconstruction
identical.

## The honest boundary: inside a run vs. across a trace

The id *values* always come from real spans. How they reach a child span differs:

- **Inside one execution** — automatic, no application help. Each span learns its
  run/trajectory id from the enclosing agent/workflow by walking LangChain's
  **run_id graph** (`parent_run_id` is handed to every callback as an explicit
  argument). This works regardless of how the spans nest, because it doesn't use
  the span tree at all.
- **Across a separate trace** (the review phase) — the application carries the
  ids forward as plain data. There is no shared context to inherit: the review
  phase is a different `graph.invoke`, and the instrumentation's in-memory run_id
  graph from phase 1 is already gone by the time phase 2 starts. So the app reads
  the active span's id while phase 1 runs (`current_span_id()` — free, see below)
  and passes it into phase 2's config `metadata` (`otel_session_id`,
  `otel_parent_trajectory_id`); the instrumentation stamps what it's given.

That second step is **application cooperation, not auto-instrumentation** — and
that's not a limitation of this approach, it is what a *run* is. A run that
pauses and resumes in another trace/process is identified by an application-level
id the app already carries to resume the work (a thread id, a checkpoint key);
here that same hand-off also carries the run/trajectory id. Generic
instrumentation can derive and propagate the ids *within* reach of a single
execution; it fundamentally cannot link two independent traces without the
application telling it they belong together.

### What depends on what (precise)

- The instrumentation code reads **no thread-local and no OTel active/ambient
  context** to do the grouping. It reads: the explicit `parent_run_id` argument,
  each span's **own** `SpanContext` (to compute its id value), and `metadata`.
- LangChain *itself* builds the `parent_run_id` graph using its own internal
  propagation; that is opaque to this instrumentation and reaches it as an
  ordinary callback argument.
- The **ATIF reconstruction** depends on neither the span tree nor any context —
  only on the attributes.

## Does it matter that the ids are `trace_id + span_id` rather than arbitrary ids?

The user's question: is a trace+span id any harder to **capture** or **pass
around** than some arbitrary id (a UUID, an app key)? Short answer: **no** for
both, and they're interchangeable for the mechanics — the differences are
secondary.

**Capturing.** A trace+span id is *already there* the instant the span starts:
`span.get_span_context()` yields a `(trace_id, span_id)` that is globally unique
by construction (128 + 64 bits), with no RNG, no allocation, and no coordination.
An arbitrary id is equally cheap to *mint* (`uuid4()`), but it is an **extra**
identifier you now have to generate and keep. So capture is a slight win for
trace+span — with two caveats: it only **exists after the span starts** (if you
need the id *before* the root span exists — e.g. to put in an inbound request
that later opens the span — an app-minted id avoids the chicken-and-egg), and if
that start span is **not sampled/recording** its context can be invalid, so you
get no id (the code returns `None`); an app id has no such dependency.

**Passing around.** **Identical.** The propagation channel carries a *string* and
does not care what the bytes mean — the run_id-graph walk (within a trace) and
the `metadata`/baggage hand-off (across a trace) move `trace-span` exactly as they
would move a UUID. Notably, *within* a trace neither needs the app to pass it
(instrumentation derives and propagates it); *across* a trace **both** need the
app to carry it. The cost is the same either way.

**So it doesn't matter for the mechanics.** It matters only for secondary
properties:

| | `trace_id + span_id` of the start span | arbitrary id (UUID / app key) |
| --- | --- | --- |
| Allocation | none — reuse what exists | must mint + store one more id |
| Uniqueness | intrinsic | intrinsic for UUIDv4; your problem otherwise |
| Back-correlation | **free** — the run id *is* a pointer to the originating span/trace; pivot OTel ↔ ATIF directly | none — an opaque token unless you also store the mapping |
| Available before the span exists | no | yes |
| Survives re-tracing / sampling-out of the start span | no (id is gone / never formed) | yes (independent of telemetry) |
| Couples run identity to telemetry ids | yes | no |

**Recommendation.** For a value that is *born at a span* — a run starts when the
workflow span starts, a trajectory starts when the agent span starts — deriving
the id from that span's `trace_id+span_id` is the natural, zero-cost,
self-correlating choice, and no harder to pass around than any other string. Pick
an application-minted id instead when the identifier must exist *before* any span,
or must survive re-instrumentation/sampling. The two compose: this prototype
**derives from trace+span by default and lets the application override via
`metadata`** — so a durable/resumed run can supply its own stable run id when the
originating span is long gone.

## Status

- Opt-in (`OTEL_INSTRUMENTATION_GENAI_EMIT_RUN_CORRELATION`); default off → no
  change to existing telemetry. The instrumentation's unit suite stays green
  (150 passed; the 4 conformance failures are pre-existing on the branch and
  unrelated to this change).
- Fully offline and deterministic (local fake OpenAI server, canned completions).
- Prototype only — `gen_ai.session.id` / `gen_ai.trajectory.id` /
  `gen_ai.trajectory.parent.id` are **not** registered GenAI attributes; this
  demonstrates the idea behind the parent doc's "run id has no OTel source" gap.
