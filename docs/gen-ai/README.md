<!--- Hugo front matter used to generate the website version of this page:
linkTitle: Generative AI
--->

# Semantic conventions for generative AI systems

**Status**: [Development][DocumentStatus]

Semantic conventions for Generative AI are defined for the following operations.

Model operations:

* [Client inference](client-inference/README.md)
* [Client realtime inference](client-realtime-inference/README.md)
* [Client embeddings](client-embeddings/README.md)
* [Client fetch response](client-fetch-response/)
* [Server inference](server-inference/)
* [Execute tool](execute-tool/README.md)
* [LLM call examples](non-normative/examples-llm-calls.md)

Agentic operations:

* [Client create agent](client-create-agent/)
* [Client invoke agent](client-invoke-agent/README.md)
* [Invoke agent](invoke-agent/)
* [Plan](plan/)
* [Execute tool](execute-tool/README.md)
* [Retrieval](retrieval/README.md)
* [Client memory](client-memory/)
* [Agent call examples](non-normative/examples-agent-calls.md)

Protocols:

* [Model Context Protocol (MCP)](../mcp/README.md)
* [Agent2Agent Protocol (A2A)](../a2a/README.md)

Technology specific semantic conventions are defined for the following GenAI system:

* [Anthropic](./anthropic.md): Semantic Conventions for Anthropic.
* [Azure AI Inference](./azure-ai-inference.md): Semantic Conventions for Azure AI Inference.
* [AWS Bedrock](./aws-bedrock.md): Semantic Conventions for AWS Bedrock.
* [OpenAI](./openai.md): Semantic Conventions for OpenAI.

See also:

* [Evaluation](evaluation/): Semantic Conventions for Generative AI evaluation results - *events*.
* [Events](gen-ai-events.md): Semantic Conventions for Generative AI inputs and outputs - *events*.
* [Exceptions](gen-ai-exceptions.md): Semantic Conventions for Generative AI *exceptions*.
* [Metrics](gen-ai-metrics.md): Semantic Conventions for Generative AI operations - *metrics*.

## Attributes shared across operations

Instrumentations MAY propagate context containing attributes listed below to nested
instrumentations within the same process. This allows queries to select related
spans without traversing the hierarchy.

When an attribute is available both from the instrumented library and from outer
context, instrumentation SHOULD prefer the library's value.

Instrumentations SHOULD NOT propagate attributes not listed here.
Instrumentations SHOULD NOT use these attributes on signals that don't reference them
explicitly.

* [`gen_ai.conversation.id`](/docs/registry/attributes/gen-ai.md#gen-ai-conversation-id)

## Capturing instructions, inputs, and outputs

### Full (buffered) content

Model instructions, user messages, and model outputs are considered sensitive and
are often large in size.

Recording large or sensitive content in telemetry may be problematic due to high
storage costs, regulatory requirements, or the need to enforce different access
models for operational and user data.

OpenTelemetry instrumentations SHOULD NOT capture them by default, but SHOULD
provide an option for users to opt in.

Application developers should choose an appropriate usage pattern based on
application needs and maturity:

1. [Default] Don't record instructions, inputs, or outputs.
2. Record instructions, inputs, and outputs on the GenAI spans using corresponding
   attributes (`gen_ai.system_instructions`, `gen_ai.input.messages`,
   `gen_ai.output.messages`).

   This approach is best suited for situations where telemetry volume is manageable
   and either privacy regulations do not apply or the telemetry storage complies
   with them, for example, in pre-production environments.

   See [Recording content on attributes](#recording-content-on-attributes)
   section for more details.
3. Store content externally and record references on the spans.

   This pattern is recommended in production environments where telemetry volume
   is a concern or sensitive data needs to be handled securely. Using external
   storage enables separate access controls.

   See [Uploading content to external storage](#uploading-content-to-external-storage)
   section for more details.

#### Recording content on attributes

The content captured in `gen_ai.system_instructions`, `gen_ai.input.messages`,
and `gen_ai.output.messages` attributes is likely to be large.

It may contain media, and even in the text form, it may be larger than
observability backend limits for telemetry envelopes or attribute values.

The inputs and outputs attributes follow common structure
formally defined in [inputs JSON schema](/model/gen-ai/gen-ai-input-messages.json) and
[outputs JSON schema](/model/gen-ai/gen-ai-output-messages.json). See also their representation
in [Python code](./non-normative/models.py).

These attributes MUST be recorded as
[AnyValue](https://opentelemetry.io/docs/specs/otel/common/#anyvalue) values
conforming to their JSON schemas.

The JSON schemas describe the structure of these attribute values in the
OpenTelemetry data model, not an export format or encoding. Producers SHOULD
use them as a reference for modeling values with language-specific `AnyValue`
types. For example, a property with `"format": "binary"` SHOULD be recorded as
a byte array, not a string.

Instrumentation MAY provide a configuration option allowing to truncate properties
such as individual message contents, preserving JSON structure.

##### Content capture configuration

Capturing model instructions, prompts, completions, retrieval queries, prompt template variables, and memory records is gated by an explicit user opt-in.
Instrumentations that support capturing content MUST provide a configuration option to control
whether content is captured and which telemetry signals receive it.

The content capture configuration governs the following attributes and their representation on spans and events:

- [`gen_ai.input.messages`](/docs/registry/attributes/gen-ai.md#gen-ai-input-messages)
- [`gen_ai.output.messages`](/docs/registry/attributes/gen-ai.md#gen-ai-output-messages)
- [`gen_ai.system_instructions`](/docs/registry/attributes/gen-ai.md#gen-ai-system-instructions)
- [`gen_ai.tool.call.arguments`](/docs/registry/attributes/gen-ai.md#gen-ai-tool-call-arguments)
- [`gen_ai.tool.call.result`](/docs/registry/attributes/gen-ai.md#gen-ai-tool-call-result)
- [`gen_ai.retrieval.query.text`](/docs/registry/attributes/gen-ai.md#gen-ai-retrieval-query-text)
- [`gen_ai.prompt.variables`](/docs/registry/attributes/gen-ai.md#gen-ai-prompt-variables)
- [`gen_ai.memory.query.text`](/docs/registry/attributes/gen-ai.md#gen-ai-memory-query-text)
- [`gen_ai.memory.records`](/docs/registry/attributes/gen-ai.md#gen-ai-memory-records)

Attributes providing schemas rather than user/model payload content (such as [`gen_ai.tool.definitions`](/docs/registry/attributes/gen-ai.md#gen-ai-tool-definitions)) are not governed by this configuration.

A content attribute MUST NOT be reported on a signal unless that signal's conventions
reference the attribute or explicitly permit copying it from another signal.
For example, [GenAI client operation exception events](gen-ai-exceptions.md#generative-ai-client-operation-exception)
MAY include attributes captured on the corresponding span when configured to do so.
In either case, the content capture configuration MUST enable content on the destination signal.

If this configuration is provided via an environment variable, the environment variable MUST be
named `OTEL_INSTRUMENTATION_GENAI_CAPTURE_CONTENT`.

The configuration MUST support the following values:

| Value | Behavior |
| --- | --- |
| `NO_CONTENT` | Do not capture content on spans or events. (Default) |
| `SPAN_ONLY` | Capture content on spans only. |
| `EVENT_ONLY` | Capture content on events only. |
| `SPAN_AND_EVENT` | Capture content on both spans and events. |

Environment variable value SHOULD be parsed case-insensitively.

If an unrecognized or invalid value is provided, instrumentations SHOULD default to `NO_CONTENT`.

#### Uploading content to external storage

Instrumentations MAY support user-defined in-process hooks to handle content upload.
Uploading content and emitting external references SHOULD be explicitly enabled
independently of the opt-in flags that control recording
`gen_ai.system_instructions`, `gen_ai.input.messages`, `gen_ai.output.messages`,
and `gen_ai.tool.definitions` directly on telemetry signals.

If such a hook is supported and explicitly configured, instrumentations SHOULD
invoke it regardless of the span sampling decision with:

- the [instructions](/model/gen-ai/gen-ai-system-instructions.json), [inputs](/model/gen-ai/gen-ai-input-messages.json),
  [outputs](/model/gen-ai/gen-ai-output-messages.json), and
  [tool definitions](/model/gen-ai/gen-ai-tool-definitions.json) objects using the
  structures defined in this convention;
- the span instance

The hook SHOULD receive the same instructions, inputs, outputs, and tool definitions that the
instrumentation would record in these attributes.

The hook implementation SHOULD be able to enrich and modify provided span, instructions,
message, and tool definition objects.

If instrumentation is configured to also record `gen_ai.system_instructions`,
`gen_ai.input.messages`, `gen_ai.output.messages`, and
`gen_ai.tool.definitions` attributes, it SHOULD do it after calling the hook and
SHOULD record values that were potentially modified within the hook
implementation.

The hook API SHOULD be generic. The application or distro is responsible for the hook
implementation including

- the uploading process either in synchronous or asynchronous way,
- recording references to the uploaded content on the span,
- handling content in a different way.

When a hook handles content externally, it SHOULD use
`gen_ai.system_instructions_ref`, `gen_ai.input.messages_ref`,
`gen_ai.output.messages_ref`, or `gen_ai.tool.definitions_ref`. This convention
does not prescribe the URI scheme, object layout, serialization format,
retention policy, or access mechanism.

Implementations MAY use content-derived identifiers to deduplicate repeated
content, such as system instructions or tool definitions.

Application or OpenTelemetry distributions MAY also implement content uploading
in the telemetry processing pipeline (in-process or via a collector), based on the
`gen_ai.system_instructions`, `gen_ai.input.messages`, `gen_ai.output.messages`,
and `gen_ai.tool.definitions` attributes. Given the potential data volume, it is
RECOMMENDED to tune batching and export settings accordingly in the OpenTelemetry
SDK pipeline.

##### Content upload configuration

Instrumentations that support content uploading via completion hooks SHOULD support the following
standard configuration options:

- **Content hook**: Specifies the qualified method or component name to be called when an operation completes.
  - Environment variable: `OTEL_INSTRUMENTATION_GENAI_CONTENT_HOOK` (e.g. `upload`).
- **Upload base path**: Specifies the destination path or URI for uploaded prompt and response content.
  It MAY be a local filesystem directory (e.g. `/var/log/genai/prompts`) or a cloud storage URI
  (e.g. `s3://my-bucket/prompts`, `gs://my-bucket/prompts`, `az://my-container/prompts`).
  - Environment variable: `OTEL_INSTRUMENTATION_GENAI_UPLOAD_BASE_PATH`
- **Upload format**: Specifies the data serialization format for uploaded content. Supported values MUST include
  `json` and `jsonl`. Defaults to `json`.
  - Environment variable: `OTEL_INSTRUMENTATION_GENAI_UPLOAD_FORMAT`
- **Upload maximum queue size**: Specifies the maximum number of concurrent uploads to queue in background
  upload processing before dropping or throttling. Defaults to `20`.
  - Environment variable: `OTEL_INSTRUMENTATION_GENAI_UPLOAD_MAX_QUEUE_SIZE`

## How to aggregate token usage

> [!NOTE]
> Use [inference token metrics](#inference-token-metrics) (or corresponding
> [embeddings](client-embeddings/README.md#metrics) or other metrics, depending on the
> operation) whenever possible. They aren't affected by trace sampling. Filter
> or group by `service.name` if multiple services report the same operations.

To see token usage in an individual trace, filter by `gen_ai.operation.name`
and break down by `service.name` if multiple services report the same type of
spans. For example (pseudocode):

<!-- TODO: replace the gen_ai.operation.name filter with
span.type, see
https://github.com/open-telemetry/opentelemetry-specification/pull/5378 -->

```text
sum(gen_ai.usage.input_tokens)
  where trace_id == "<trace id>"
    and gen_ai.operation.name in (chat, generate_content, text_completion, realtime_inference)
  group by service.namespace, service.name
```

> [!WARNING]
> Don't sum `gen_ai.usage.*` over all spans without filtering by operation name.
> The same tokens can be reported on multiple types of spans: agent and
> inference spans, or inference spans from gateways and different layers of
> the inference infrastructure.

## Inference token metrics

The conventions described in this section are specific to Generative AI client
applications and describe how inference token metrics are reported.

Individual systems may include additional system-specific attributes.
It is recommended to check system-specific documentation, if available.

Two families of token instruments are defined:

- **Usage** (`gen_ai.client.inference.usage.*` counters) are the primary instruments
  for measuring token consumption. They track how many tokens were spent over time, spending rate,
  and serve as a proxy for cost approximation. Each token category is a separate
  monotonic counter broken down by [`gen_ai.token.modality`](/docs/registry/attributes/gen-ai.md),
  except `gen_ai.client.inference.usage.reasoning.output_tokens`.
  The `cache_read`,
  `cache_write`, and `reasoning` counters report subsets of the `input_tokens`
  and `output_tokens` counters.
- **Per-operation token distribution** (`gen_ai.client.inference.operation.input_tokens`
  and `gen_ai.client.inference.operation.output_tokens`) describe how token usage
  is distributed across individual inference operations. They should not be used
  for total usage or cost calculations. Use histograms exclusively to monitor
  usage percentiles (e.g. p95/p99) and detect outliers.

Embeddings operations only report the
[`gen_ai.client.embeddings.operation.input_tokens`](client-embeddings/metrics/gen_ai.client.embeddings.operation.input_tokens.md)
histogram, and total token usage can be computed from it.

> [!NOTE]
> 
> The `gen_ai.client.inference.operation.input_tokens` and
> `gen_ai.client.inference.operation.output_tokens` histograms are
> deliberately not broken down by modality: percentiles across modalities do
> not add up.
> 
> A query like this one appears valid:
> 
> ```promql
> histogram_quantile(0.95,
>   sum(rate({"gen_ai.client.inference.operation.input_tokens"}[5m]))
> )
> ```
> 
> However, if modality were added as a dimension, it would produce meaningless results: for
> 100 identical operations with 300 input tokens each (100 text and 200 image),
> it would return 200 instead of 300.
> 
> For the full reasoning behind this design, see
> [Token metrics design](/docs/gen-ai/non-normative/token-metrics-design.md).

[DocumentStatus]: https://opentelemetry.io/docs/specs/otel/document-status
