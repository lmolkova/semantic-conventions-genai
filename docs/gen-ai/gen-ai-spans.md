<!--- Hugo front matter used to generate the website version of this page:
linkTitle: Spans
--->

# Semantic conventions for generative client AI spans

**Status**: [Development][DocumentStatus]

<!-- toc -->

- [Spans](#spans)
  - [Inference](#inference)
  - [Embeddings](#embeddings)
  - [Retrievals](#retrievals)
  - [Fetch response](#fetch-response)
    - [Event: `gen_ai.client.fetch_response.exception`](#event-gen_aiclientfetch_responseexception)
  - [Memory](#memory)
  - [Execute tool span](#execute-tool-span)
- [Capturing instructions, inputs, and outputs](#capturing-instructions-inputs-and-outputs)
  - [Full (buffered) content](#full-buffered-content)
    - [Recording content on attributes](#recording-content-on-attributes)
    - [Uploading content to external storage](#uploading-content-to-external-storage)
  - [Streaming chunks](#streaming-chunks)

<!-- tocstop -->

## Spans

GenAI spans represent logical operations as observed by the caller.
They SHOULD cover the duration of the operation, starting when it is
initiated and ending when the response is fully received or the operation
is terminated due to an error or cancellation.

If a transient issue happened and the request was retried automatically, the
corresponding span SHOULD cover the duration of the logical operation with all
retries.

### Inference

Inference span and metric conventions are defined in [Client Inference](client-inference/README.md).

### Embeddings

Embeddings span and metric conventions are defined in [Client Embeddings](client-embeddings/README.md).

### Retrievals

Retrieval span and metric conventions for GenAI frameworks and applications
are defined in [Retrieval](retrieval/README.md).

### Fetch response

See [`gen_ai.fetch_response.client`](client-fetch-response/spans/gen_ai.fetch_response.client.md) for the definition.

#### Event: `gen_ai.client.fetch_response.exception`

See [`gen_ai.client.fetch_response.exception`](client-fetch-response/events/gen_ai.client.fetch_response.exception.md) for the definition.

### Memory

See [`gen_ai.memory.client`](client-memory/spans/gen_ai.memory.client.md) for the definition.

### Execute tool span

Execute tool span, event, and metric conventions are defined in [Execute Tool](execute-tool/README.md).

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

Check out [LLM call examples](./non-normative/examples-llm-calls.md).

### Streaming chunks

TODO

[DocumentStatus]: https://opentelemetry.io/docs/specs/otel/document-status
