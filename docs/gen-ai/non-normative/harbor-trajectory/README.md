<!-- I'm an AI agent!!! -->
# Mapping OpenTelemetry GenAI telemetry to the Harbor ATIF trajectory format

This is a non-normative guide. It shows how telemetry captured with the
[OpenTelemetry GenAI semantic conventions](../../gen-ai-spans.md) in this repo
can be converted into a
[Harbor **ATIF** (Agent Trajectory Interchange Format) v1.7](https://github.com/harbor-framework/harbor/blob/main/rfcs/0001-trajectory-format.md)
trajectory, and where the conventions do **not** define a source for an ATIF
field.

Everything here is derived from a runnable scenario, not hand-authored:

| File | What it is |
| --- | --- |
| [scenario.py](scenario.py) | A multi-agent + orchestrator scenario that emits real OTel spans following these conventions |
| [captured-otel-spans.json](captured-otel-spans.json) | The spans actually emitted by that scenario |
| [otel_to_atif.py](otel_to_atif.py) | A mechanical OTel→ATIF converter |
| [sample-trajectory.atif.json](sample-trajectory.atif.json) | The ATIF trajectory produced from the captured spans |

Reproduce:

```bash
uv run --with opentelemetry-sdk python scenario.py captured-otel-spans.json
python3 otel_to_atif.py captured-otel-spans.json sample-trajectory.atif.json
```

## ATIF in brief

- **Use case.** ATIF is Harbor's interchange format for recording agent runs so
  they can be replayed, evaluated, and used as RL/SFT training data.
- **Trajectory.** One agent's run captured as a linear, ordered list of `steps`
  (system/user/agent turns, tool calls, observations) plus the agent's identity
  and metrics. It is the unit *document* of the format.
- **Trajectories per run.** A run produces **one or more** trajectories: a root
  trajectory, one embedded sub-trajectory per sub-agent, and a new segment each
  time context management splits the run (`continued_trajectory_ref`). So one
  run → many trajectories.
- **Run-scoped vs document-scoped.** `session_id` is **run-scoped** — shared by
  every trajectory of the same run. `trajectory_id` is **document-scoped** —
  unique per trajectory and the key used to resolve sub-agent references.

## OTel vs ATIF

In plain terms, the two formats record different things for different reasons:

| | OpenTelemetry | ATIF |
| --- | --- | --- |
| **What it records** | *Everything that happened* — every operation, across the whole system | *What the agents did* — the agent/step/tool storyline |
| **How causation is expressed** | Span/parent IDs in a trace | The trajectory tree (root → sub-agents) |
| **What it's optimized for** | Fast, low-overhead emission at runtime | Consumption — a buffered, complete document |
| **Effect of infrastructure** | Shape varies with infra — where code runs, how it's hosted, agents local vs remote | Shape is infra-independent — same trajectory regardless of deployment |

## Legend

| Symbol | Meaning |
| --- | --- |
| ✅ | **Available from OTel telemetry** — a `gen_ai.*` attribute, or derivable from the trace structure (span IDs, span timing, the span tree, counting child spans) |
| ❌ | **No source** in OTel or these conventions — cannot be populated from telemetry |
| 🔌 | **Not available on the client side** — the data lives only inside the provider/inference server and never reaches a generic client instrumentation. Not a semconv gap. |
| N/A | **Not a mapping concern** — a storage/serialization or pipeline decision the producer makes, not something derived from telemetry. |
| ❓ | **Open question** — the right source is not yet decided; the converter uses a placeholder so the sample stays valid. |

## The example: two agents under an orchestrator

The scenario is a workflow that orchestrates two sub-agents and a tool. The
emitted span tree:

```text
invoke_workflow research-assistant  gen_ai.operation.name=invoke_workflow  (orchestrator)
├─ plan research-assistant          gen_ai.operation.name=plan
├─ invoke_agent researcher          gen_ai.operation.name=invoke_agent     (sub-agent 1)
│  ├─ chat gpt-4o-mini              gen_ai.operation.name=chat             -> tool_call
│  ├─ execute_tool web_search       gen_ai.operation.name=execute_tool
│  └─ chat gpt-4o-mini              gen_ai.operation.name=chat             -> findings
└─ invoke_agent writer              gen_ai.operation.name=invoke_agent     (sub-agent 2)
   └─ chat gpt-4o-mini              gen_ai.operation.name=chat             -> final brief (+ reasoning)
```

ATIF is a **linear list of steps per agent** with embedded sub-trajectories;
OTel is a **span tree**. The conversion therefore:

1. maps the `invoke_workflow` span to the **root trajectory**;
2. maps each child `invoke_agent` span to an embedded **sub-trajectory** in
   `subagent_trajectories`, linked from a root step via `subagent_trajectory_ref`;
3. flattens each agent's child `chat` / `execute_tool` spans into that agent's
   linear `steps`.

<details>
<summary>ATIF trajectory for this run (click to expand)</summary>

This is the same run as an ATIF document, in the style of Harbor's own
examples. `session_id` and the `trajectory_id`s are **invented** (no OTel
source — `session_id` is a gap, `trajectory_id` is an open question). Fields
with no client-side source — cost, token ids, logprobs — are simply **omitted**,
not faked.

```json
{
  "schema_version": "ATIF-v1.7",
  "trajectory_id": "traj-root",
  "session_id": "run_7f3a2c91",
  "agent": {
    "name": "research-assistant",
    "version": "0.3.0"
  },
  "steps": [
    {
      "step_id": 1,
      "source": "user",
      "message": "Write a 2-sentence brief on the benefits of rooftop solar for homeowners."
    },
    {
      "step_id": 2,
      "source": "agent",
      "llm_call_count": 1,
      "message": "Plan: (1) use the researcher agent to gather facts on rooftop solar benefits; (2) use the writer agent to turn the findings into a 2-sentence brief."
    },
    {
      "step_id": 3,
      "source": "agent",
      "llm_call_count": 0,
      "message": "Delegating to the researcher agent to gather facts on rooftop solar.",
      "observation": {
        "results": [
          {
            "subagent_trajectory_ref": [
              {
                "trajectory_id": "traj-researcher"
              }
            ]
          }
        ]
      }
    },
    {
      "step_id": 4,
      "source": "agent",
      "llm_call_count": 0,
      "message": "Delegating to the writer agent to compose the final brief.",
      "observation": {
        "results": [
          {
            "subagent_trajectory_ref": [
              {
                "trajectory_id": "traj-writer"
              }
            ]
          }
        ]
      }
    },
    {
      "step_id": 5,
      "source": "agent",
      "llm_call_count": 0,
      "message": "Rooftop solar can cut a household's electricity bills by roughly half, delivering substantial long-term savings. It also tends to raise a home's resale value, making it both an operational and an investment win for homeowners."
    }
  ],
  "subagent_trajectories": [
    {
      "schema_version": "ATIF-v1.7",
      "trajectory_id": "traj-researcher",
      "session_id": "run_7f3a2c91",
      "agent": {
        "name": "researcher",
        "version": "1.2.0",
        "model_name": "openai/gpt-4o-mini",
        "tool_definitions": [
          {
            "type": "function",
            "function": {
              "name": "web_search",
              "description": "Search the web for up-to-date information.",
              "parameters": {
                "type": "object",
                "properties": {
                  "query": {
                    "type": "string"
                  }
                },
                "required": [
                  "query"
                ]
              }
            }
          }
        ]
      },
      "steps": [
        {
          "step_id": 1,
          "source": "system",
          "message": "You are a research assistant. Use web_search to find facts, then summarize."
        },
        {
          "step_id": 2,
          "source": "user",
          "message": "Write a 2-sentence brief on the benefits of rooftop solar for homeowners."
        },
        {
          "step_id": 3,
          "source": "agent",
          "model_name": "gpt-4o-mini",
          "message": "",
          "metrics": {
            "prompt_tokens": 95,
            "completion_tokens": 18,
            "cached_tokens": 0
          },
          "llm_call_count": 1,
          "tool_calls": [
            {
              "tool_call_id": "call_ws_01",
              "function_name": "web_search",
              "arguments": {
                "query": "rooftop solar benefits homeowners"
              }
            }
          ],
          "observation": {
            "results": [
              {
                "source_call_id": "call_ws_01",
                "content": "Rooftop solar cuts electricity bills by ~50% on average and can raise home resale value."
              }
            ]
          }
        },
        {
          "step_id": 4,
          "source": "agent",
          "model_name": "gpt-4o-mini",
          "message": "Rooftop solar typically reduces electricity bills by about half and tends to increase a home's resale value.",
          "metrics": {
            "prompt_tokens": 140,
            "completion_tokens": 32,
            "cached_tokens": 88
          },
          "llm_call_count": 1
        }
      ],
      "final_metrics": {
        "total_prompt_tokens": 235,
        "total_completion_tokens": 50,
        "total_cached_tokens": 88,
        "total_steps": 4
      }
    },
    {
      "schema_version": "ATIF-v1.7",
      "trajectory_id": "traj-writer",
      "session_id": "run_7f3a2c91",
      "agent": {
        "name": "writer",
        "version": "1.0.0",
        "model_name": "openai/gpt-4o-mini"
      },
      "steps": [
        {
          "step_id": 1,
          "source": "system",
          "message": "You are a concise technical writer. Produce a polished 2-sentence brief."
        },
        {
          "step_id": 2,
          "source": "user",
          "message": "Rooftop solar typically reduces electricity bills by about half and tends to increase a home's resale value."
        },
        {
          "step_id": 3,
          "source": "agent",
          "model_name": "gpt-4o-mini",
          "message": "Rooftop solar can cut a household's electricity bills by roughly half, delivering substantial long-term savings. It also tends to raise a home's resale value, making it both an operational and an investment win for homeowners.",
          "metrics": {
            "prompt_tokens": 60,
            "completion_tokens": 55,
            "cached_tokens": 0
          },
          "llm_call_count": 1,
          "reasoning_effort": "medium",
          "reasoning_content": "Combine the savings and resale points into two crisp sentences."
        }
      ],
      "final_metrics": {
        "total_prompt_tokens": 60,
        "total_completion_tokens": 55,
        "total_cached_tokens": 0,
        "total_steps": 3
      }
    }
  ]
}
```

</details>

## Field-by-field mapping

### Root `Trajectory`

| ATIF field | Source | Notes |
| --- | --- | --- |
| `schema_version` | constant | `"ATIF-v1.7"`; not telemetry. |
| `session_id` | ❌ | ATIF `session_id` is the **run** (shared across a run's trajectories). The conventions define **no agent-run identifier**. `trace_id` is a transport/sampling construct, not a run — a run may span several traces and a trace may hold several runs — so it can't stand in. `gen_ai.conversation.id` is a different, *broader* scope (the conversation/thread, which can drive many runs). The captured `conversation.id` is kept in the root `extra` for traceability. |
| `trajectory_id` | ❓ open | A per-document unique id and the **resolution key** for `subagent_trajectory_ref`. The right OTel source is **not yet decided** — `span_id` is a candidate (the converter uses it as a placeholder so refs resolve), but we are not asserting that mapping; `trace_id` is wrong (a trace can hold many trajectories). To be explored. |
| `agent` | see [AgentSchema](#agentschema) | For the root, the `invoke_workflow` span. |
| `steps` | derived | See [step flattening](#stepobject). |
| `subagent_trajectories[]` | ✅ span tree | Each child `invoke_agent` span → one embedded sub-trajectory (its `trajectory_id` source is the open question above). |
| `notes` | constant | Optional free text. |
| `final_metrics` | ✅ | See [FinalMetricsSchema](#finalmetricsschema). |
| `continued_trajectory_ref` | N/A | A **storage concern**: whether a run is split across multiple trajectory documents is decided by the producer when serializing, not derived from telemetry. Set it (or not) at write time. |
| `extra` | — | Free-form; used here to flag the workflow-vs-agent mismatch (below). |

### AgentSchema

| ATIF field | Source | Notes |
| --- | --- | --- |
| `name` | ✅ `gen_ai.agent.name` (agents) / `gen_ai.workflow.name` (root) | |
| `version` | ✅ `gen_ai.agent.version` | Populated for the root too, under the *blend* assumption that an agent-driven `invoke_workflow` span carries agent attributes (see below). |
| `model_name` | ✅ `gen_ai.request.model` | Set only when the actor runs inference. A deterministic orchestrator has no model, so it stays unset on the root; an LLM-driven orchestrator would set it. |
| `tool_definitions[]` | ✅ `gen_ai.tool.definitions` (reshaped) | **Different shape**: semconv is flat (`{type, name, description, parameters}`); ATIF wants OpenAI-nested (`{type:"function", function:{…}}`). The converter reshapes — mechanical and lossless, but *not* a verbatim copy. |
| `extra` | ✅ `gen_ai.agent.description` | No dedicated ATIF description field; placed in `extra`. |

### StepObject

Steps are reconstructed per agent from `gen_ai.system_instructions`, each
`chat` span's `gen_ai.input.messages` / `gen_ai.output.messages`, and the
`execute_tool` spans.

| ATIF field | Source | Notes |
| --- | --- | --- |
| `step_id` | ✅ derived | Sequential index over the reconstructed steps. |
| `timestamp` | ✅ span start time | The span's start time is a faithful step timestamp. |
| `source` | ✅ message `role` | `system`→`system`, `user`→`user`, `assistant`→`agent`. The `tool` role becomes an `observation` on the calling agent step, not a step. |
| `message` | ✅ message `parts[].content` (`type:"text"`) | |
| `model_name` | ✅ `gen_ai.request.model` | |
| `reasoning_effort` | ✅ `gen_ai.request.reasoning.level` | |
| `reasoning_content` | ✅ `parts[]` with `type:"reasoning"` | `reasoning`/`thinking` part types are defined in the message schemas. |
| `tool_calls[]` | ✅ `parts[]` with `type:"tool_call"` | See [ToolCallSchema](#toolcallschema). |
| `observation` | ✅ `execute_tool` span / `tool_call_response` parts | See [ObservationSchema](#observationschema). |
| `metrics` | ✅ / ❌ | See [MetricsSchema](#metricsschema). |
| `llm_call_count` | ✅ derived (count of child `chat` spans) | `1` per inference; `0` for deterministic dispatch; `1` for the `plan` step. This per-invocation count is being standardized as a **metric** in open PR [#336](https://github.com/open-telemetry/semantic-conventions-genai/pull/336) — `gen_ai.agent.inference_calls_per_invocation` (histogram, number of model calls per agent invocation) — and the same value could equally be expressed as a span **attribute**. Scope differs: the metric is per agent invocation; ATIF's is per step. |
| `is_copied_context` | N/A | Training-pipeline flag (exclude copied steps from SFT data); set by the producer at write time, not derived from telemetry. |
| `extra` | — | Used to tag the `plan` step type (below). |

### ToolCallSchema

| ATIF field | Source | Notes |
| --- | --- | --- |
| `tool_call_id` | ✅ `tool_call` part `id` (= `gen_ai.tool.call.id`) | |
| `function_name` | ✅ `tool_call` part `name` (= `gen_ai.tool.name`) | |
| `arguments` | ✅ `tool_call` part `arguments` (= `gen_ai.tool.call.arguments`) | |

### ObservationSchema / ObservationResultSchema

| ATIF field | Source | Notes |
| --- | --- | --- |
| `results[].source_call_id` | ✅ `gen_ai.tool.call.id` | Correlates the result to the `tool_call`. Omitted for workflow dispatch (not an LLM tool call). |
| `results[].content` | ✅ `gen_ai.tool.call.result` / `tool_call_response` part `response` | |
| `results[].subagent_trajectory_ref[]` | ✅ span tree | A child `invoke_agent` span → embedded sub-trajectory; the ref's `trajectory_id` uses the same placeholder as the [open question](#root-trajectory) above. |

### MetricsSchema

| ATIF field | Source | Notes |
| --- | --- | --- |
| `prompt_tokens` | ✅ `gen_ai.usage.input_tokens` | |
| `completion_tokens` | ✅ `gen_ai.usage.output_tokens` | |
| `cached_tokens` | ✅ `gen_ai.usage.cache_read.input_tokens` | Defined; not emitted in this scenario, so shown as `CANT_POPULATE`. |
| `cost_usd` | ❌ | No cost attribute in the conventions. |
| `prompt_token_ids` | 🔌 | Integer tokenizer IDs. Not returned by client APIs (e.g. OpenAI exposes token *strings*/*bytes*, never vocab IDs); only the inference server that owns the tokenizer has them. |
| `completion_token_ids` | 🔌 | Same — not available to client-side instrumentation. |
| `logprobs` | ❌ | Output logprob *values* **are** returnable client-side (OpenAI `logprobs: true`), but no `gen_ai.*` attribute models them — a genuine semconv gap, not a client-availability one. |
| `extra.reasoning_output_tokens` | ✅ `gen_ai.usage.reasoning.output_tokens` | No native ATIF field; placed in `extra`. |

### ContentPartSchema

| ATIF | Source | Notes |
| --- | --- | --- |
| `type:"text"` | ✅ `text` part | |
| `type:"image"` + `source.{media_type,path}` | ❌ (mostly) | Only an **image-typed `uri` part** maps (`uri`→`path`, `mime_type`→`media_type`). The semconv `blob` part is **inline bytes** (no path), `file` is a provider **`file_id`** (not a path/URL), and parts may be **any modality** (audio/video/pdf) — none of which ATIF's image-only, path-based content part can represent. Not exercised in this scenario. |

### FinalMetricsSchema

| ATIF field | Source | Notes |
| --- | --- | --- |
| `total_prompt_tokens` | ✅ agent-span `gen_ai.usage.input_tokens` (or summed from `chat` spans) | |
| `total_completion_tokens` | ✅ agent-span `gen_ai.usage.output_tokens` | |
| `total_cached_tokens` | ✅ sum of `gen_ai.usage.cache_read.input_tokens` | Derivable by summing; none emitted in this scenario, so absent from the sample. |
| `total_cost_usd` | ❌ | No cost attribute. |
| `total_steps` | ✅ derived | Count of reconstructed steps. |

## Gaps at a glance (❌)

These ATIF fields have **no source** in the GenAI conventions and are
`CANT_POPULATE` in the sample:

- **Run id (`session_id`)** — no convention identifies an agent *run*; `trace_id` is transport, `conversation.id` is the broader thread.
- **Cost** — `metrics.cost_usd`, `final_metrics.total_cost_usd`.
- **Logprobs** — `metrics.logprobs`: returnable client-side but unmodeled by `gen_ai.*`.
- **Plan content** — the `plan` span defines no message attributes today; this sample assumes a fix (see the *plan content* note above). Without it, the plan output is not capturable on the `plan` span.

**IDEA: blend agent and workflow spans.** Treat an agent-driven `invoke_workflow`
span as a special kind of `invoke_agent` span that may carry the agent attributes
(`gen_ai.agent.version`, `gen_ai.agent.description`, and `gen_ai.request.model`
when the orchestrator runs inference). That removes the "workflow has no
`version`/`model_name`" gap entirely — the root maps like any other agent. This
sample adopts the idea: the root `version`/`description` are populated from the
workflow span; `model_name` stays unset only because this orchestrator is
deterministic.
- BUG: plan span has no input/output

Several ✅ fields come from the trace *structure* rather than a single attribute
— `timestamp` (span start), `step_id`/`total_steps` (counting), `llm_call_count`
(counting `chat` spans), and `subagent_trajectories` / `subagent_trajectory_ref`
(the span tree). `trajectory_id` is left open (❓).

Fields that are not gaps either, but are **not available on the client side**
(🔌) and appear as `NOT_AVAILABLE_CLIENT_SIDE`: `metrics.prompt_token_ids` and
`metrics.completion_token_ids`. These integer tokenizer IDs exist only inside the
inference server; client APIs never return them, so no instrumentation at the
client boundary can record them — regardless of what the conventions define.

## Glossary (ATIF terms)

| Term | Meaning |
| --- | --- |
| **Run** | One logical end-to-end agent execution, identified by `session_id` (**run-scoped**). A run can span many trajectories in three shapes: **(1) one root + nested sub-agents** — the case our example shows (`traj-root` with `traj-researcher`/`traj-writer` under it); **(2) continuation segments** — the run split across several documents chained by `continued_trajectory_ref`, all sharing the `session_id`, so the "root" is a *sequence* of trajectories, not one; **(3) sibling roots** — multiple independent top-level trajectories belonging to the same run. |
| **Document** | A single trajectory object/file — the serialization unit. Identified by `trajectory_id` (**document-scoped**), which is unique per document. |
| **Trajectory** | One agent's run as a self-contained document: an `agent` plus an ordered list of `steps`. The unit of the format. |
| **Step** | One entry in a trajectory's timeline (`source` = `system` / `user` / `agent`), carrying a `message` and optionally `tool_calls`, an `observation`, `metrics`, and reasoning. |
| **`agent`** | The actor a trajectory belongs to: `name`, `version`, `model_name`, `tool_definitions`. |
| **`tool_call`** | An agent step's request to invoke a tool: `tool_call_id`, `function_name`, `arguments`. |
| **`observation`** | The result(s) returned to an agent step — tool outputs (correlated by `source_call_id`) and/or sub-agent references. |
| **`subagent_trajectories`** | Embedded child trajectories (one per sub-agent), each a complete trajectory with its own `trajectory_id`. |
| **`subagent_trajectory_ref`** | A pointer from an observation to a sub-agent trajectory, resolved by `trajectory_id` (or `trajectory_path`). |
| **`session_id`** | Run-scoped id; shared by all trajectories of one run. Not a resolution key. |
| **`trajectory_id`** | Document-scoped unique id; the key used to resolve `subagent_trajectory_ref`. |
| **`continued_trajectory_ref`** | Link to the next trajectory file when a run is split across documents (e.g. by context compaction). |


Run (session-id)
  root trajectory-1 (agent 1)
    step 1
    step 2
    sub-trajectory 1 (sub-agent 1)
    sub-trajectory 2 (sub agent 2)
  root trajectory-2 (agent 2)
    ...

## Context: trace context vs trajectory id — possible edge cases

Everything above assumed the tidy case: one run is one trace, and a trajectory
is one span subtree inside it. In practice the two identifier systems
**cross-cut**, because they measure different things:

- **Trace context** (`trace_id` / `span_id`, propagated as
  [W3C `traceparent`](https://www.w3.org/TR/trace-context/)) is a *transport*
  construct: it follows one execution as it flows through processes. A trace is
  just the spans that share a `trace_id` — nothing stops you adding more later —
  but it's treated as **bounded in practice** (backends assemble and age out a
  trace within a window), and to attach a span to it you must carry its
  `trace_id`+`span_id` forward yourself.
- **A run** (ATIF `session_id`) is an *application* construct: one logical
  end-to-end agent execution. It can pause for days, resume in a different
  process, and fan back in — still "the same run."

So all three cardinalities below are real. The stable identifier across a whole
run is the **run / `session_id`** (carried in app state or baggage), **not** the
`trace_id`.

| Edge case | Cardinality | Driven by |
| --- | --- | --- |
| [Human-in-the-loop pause/resume](#1-one-run-many-traces--human-in-the-loop) | **one run → many traces** | a real-time gap; resumption is a fresh entry point |
| [Batch fan-out](#2-one-trace-many-runs--batch-fan-out) | **one trace → many runs** | one request spawns many independent agent executions |
| [Durable / distributed execution](#3-one-run-many-span-ids--durable--distributed-execution) | **one run → many span ids** | the run is replayed / resumed across processes and workers |

### 1. One run, many traces — human-in-the-loop

> A support agent drafts a refund, then **pauses for human approval**. The
> reviewer logs in two hours later, sees a notification, clicks *Approve*; the
> agent resumes and issues the refund.

The first trace ends when the agent suspends — nothing keeps it open across a
two-hour wait. The approval arrives as a **new request → new `trace_id`**. Both
traces belong to one run.

- What survives the gap is durable state the framework persists explicitly:
  LangGraph
  [`interrupt()` + `Command(resume=…)`](https://docs.langchain.com/oss/python/langgraph/interrupts)
  over a checkpointed
  [`thread_id`](https://docs.langchain.com/oss/python/langgraph/persistence);
  OpenAI Agents'
  [human-in-the-loop](https://openai.github.io/openai-agents-js/guides/human-in-the-loop/)
  `RunState`, which "can be serialized to a string for storage in a database,
  allowing for approvals that take hours or days"; OpenAI Assistants, where a run
  enters
  [`requires_action` and continues the **same run**](https://developers.openai.com/api/docs/guides/agents/running-agents)
  after `submit_tool_outputs`.
- In OTel the resumption is usually a **new trace**, linked back to the
  suspending span with a
  [span link](https://opentelemetry.io/docs/concepts/signals/traces/#span-links)
  rather than parented under it — the resuming request is a fresh entry point, and
  a new bounded trace keeps a multi-hour gap out of one ever-growing trace. (You
  *could* reuse the original `trace_id` instead; you'd just have to carry it and
  the parent `span_id` across the gap. Replay-based engines reconstruct the work
  into one trace; see case 3.)
- In ATIF this is one run (`session_id`) whose timeline is split into
  **continuation segments** chained by `continued_trajectory_ref`.

### 2. One trace, many runs — batch fan-out

> A nightly job gets one request — "triage these 100 tickets" — and **fans out**
> one independent agent run per ticket.

A single entry point (one `trace_id`) dispatches N self-contained runs. Each has
its own inputs, its own `session_id`, its own success/failure; they only share a
dispatching parent. Patterns:
[LangGraph `Send` / map-reduce](https://docs.langchain.com/oss/python/langgraph/use-graph-api),
[AWS Step Functions Distributed Map](https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html),
the [OpenAI Batch API](https://developers.openai.com/api/docs/guides/batch).

- For a small fan-out the N runs are just child subtrees of the one trace. At
  scale you give each run its **own** trace and link it back (to keep traces
  bounded) — but nothing *requires* that; one trace holding many runs is the
  natural first form.
- In ATIF each run is its own top-level trajectory (its own `session_id`). The
  batch has no single ATIF home — it is a grouping *above* the run, the same
  mismatch `invoke_workflow` already has (ATIF has no generic grouping node).

### 3. One run, many span ids — durable / distributed execution

> *Can many `span_id`s capture one run?* **Always** — even the simple example is
> many span_ids (workflow + agents + chat + tools). The real question is whether
> they sit in **one trace** or **several**. That splits into two layers:

**Durability layer — one run spans many process executions (universal).** Durable
engines re-run the same logical run across separate process invocations, replaying
persisted state and skipping completed steps. The stable identity is the engine's
*run id*, never a `trace_id`:

- [Temporal](https://docs.temporal.io/workers) — stateless workers; a blocked
  Workflow Execution "can be resurrected on the same or different Worker," recovered
  by [replaying its Event History](https://docs.temporal.io/encyclopedia/event-history).
- [Restate](https://docs.restate.dev/guides/request-lifecycle) — replays an
  invocation's journal on each attempt, resuming "from exactly where it left off."
- [Inngest](https://www.inngest.com/docs/learn/how-functions-are-executed) — "each
  step ... is executed as a separate HTTP request"; the function is re-executed with
  prior step results memoized.
- [DBOS](https://docs.dbos.dev/production/workflow-recovery) — recovers a workflow on
  another executor after a crash, keyed by a durable workflow id.
- [Step Functions](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-activities.html)
  activities can wait up to a year for an external worker before the run continues.

**Tracing layer — one trace or several is framework-dependent.** Two shapes occur:

- **Reconstructed into one run-trace.** Replay engines stitch the attempts into a
  single trace: Restate models retries/resumes as `invocation-attempt` spans *within
  one trace*; Inngest shows one automatic run-trace with steps as spans; Temporal's
  [OpenTelemetry interceptor](https://docs.temporal.io/develop/python/platform/observability)
  propagates W3C context through workflow/activity headers so one Run Id's spans join
  one trace (the Python SDK even emits zero-duration, replay-suppressed spans joined by
  **span links**, because a long-lived open span isn't replay-safe). Many span_ids,
  **one** `trace_id`.
- **Separate traces joined by links.** When resumption is a fresh entry point — a human
  approving hours later, or Temporal
  [Continue-As-New](https://docs.temporal.io/workflow-execution/continue-as-new) minting
  a **new Run Id** with fresh history — the run becomes several traces connected with
  [span links](https://opentelemetry.io/docs/concepts/signals/traces/#span-links) rather
  than a parent. (Step Functions
  [Distributed Map](https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html)
  children are separate executions X-Ray
  [doesn't trace at all](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-xray-tracing.html)
  — a reminder the run can outrun the tracing.)

**Queues force links either way.** OTel's
[messaging conventions](https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/)
correlate producer and consumer with **links, not parent-child** — "a span can only have
a single parent," and a batch consumer links to *each* message's creation context, fanning
back into *many* producer traces at once.

| System | Run identity | Tracing shape |
| --- | --- | --- |
| LangGraph / OpenAI Agents SDK | `thread_id` / serialized `RunState` | resume = new request → new trace, linked back |
| Temporal | Workflow Id + Run Id | one trace per Run Id (interceptor); Continue-As-New = new Run Id + link |
| Restate | invocation `inv_…` | one trace; attempts as spans; `send` children = linked traces |
| Inngest | run id | one run-trace; each step a separate HTTP request, shown as spans |
| Step Functions | execution ARN | one X-Ray trace; Distributed-Map children untraced |

### Why "just use one big trace" doesn't get you out of carrying an id

A trace is just the spans that share a `trace_id`; there's no "close", so you *can* emit
another span into an old trace later. But forcing a durable run into one trace doesn't make
the run-id problem go away:

- **To attach a late span you must carry the parent's `trace_id`+`span_id` forward** and set
  it as the parent. So "keep it one trace" still means propagating ids across the gap — the
  same hand-off as carrying a run id, just *with the trace+span as the id* (exactly
  [what the cross-trace demo does](cross-trace/README.md)). One trace doesn't avoid carrying
  ids; it **is** carrying ids.
- **Making the whole run one enclosing operation** would need a single span held open for the
  run's lifetime — unbounded, and not replay-safe; durable engines avoid it (Temporal's Python
  interceptor emits zero-duration spans rather than hold one open). You can add *more* spans to
  a trace, but you can't re-open an ended one.
- **A span has exactly one parent**, so fan-in (one consumer, many producers) can't be
  parent-child no matter the trace — it must be
  [links](https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/).
- **Backends bound traces operationally** — assembly windows, retention, and trace-level views
  all assume a trace finishes in a reasonable time; an ever-growing trace across long gaps is an
  operational headache, not a data-model violation.

So across a durable run you carry a **stable id forward as data** either way — the only real
choice is whether that id is the originating `trace_id+span_id` (reused as the run / trajectory
id) or a separately minted run id, and where producers fan in you also need **span links**. ATIF
records the carried id directly (`session_id`, `continued_trajectory_ref`, with
`gen_ai.conversation.id` as the broader thread above it); `trajectory_id` stays pinned to a
single span subtree, which is why it can never simply *be* the `trace_id`.
