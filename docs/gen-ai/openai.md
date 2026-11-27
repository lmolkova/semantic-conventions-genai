<!--- Hugo front matter used to generate the website version of this page:
linkTitle: OpenAI
--->

# Semantic conventions for OpenAI client operations

**Status**: [Development][DocumentStatus]

<!-- toc -->

- [Spans](#spans)
  - [Inference](#inference)
  - [Embeddings](#embeddings)
  - [Fetch response](#fetch-response)
- [Metrics](#metrics)
  - [Metric: `gen_ai.client.inference.usage.input_tokens`](#metric-gen_aiclientinferenceusageinput_tokens)
  - [Metric: `gen_ai.client.inference.usage.output_tokens`](#metric-gen_aiclientinferenceusageoutput_tokens)
  - [Metric: `gen_ai.client.inference.usage.cache_read.input_tokens`](#metric-gen_aiclientinferenceusagecache_readinput_tokens)
  - [Metric: `gen_ai.client.inference.usage.cache_write.input_tokens`](#metric-gen_aiclientinferenceusagecache_writeinput_tokens)
  - [Metric: `gen_ai.client.inference.usage.reasoning.output_tokens`](#metric-gen_aiclientinferenceusagereasoningoutput_tokens)
  - [Metric: `gen_ai.client.inference.operation.input_tokens`](#metric-gen_aiclientinferenceoperationinput_tokens)
  - [Metric: `gen_ai.client.inference.operation.output_tokens`](#metric-gen_aiclientinferenceoperationoutput_tokens)
  - [Metric: `gen_ai.client.operation.duration`](#metric-gen_aiclientoperationduration)
  - [Metric: `gen_ai.client.inference.duration`](#metric-gen_aiclientinferenceduration)
<!-- tocstop -->

The Semantic Conventions for [OpenAI](https://openai.com/) extend and override the [Gen AI Semantic Conventions](/docs/README.md).

## Spans

`gen_ai.provider.name` MUST be set to `"openai"`.

### Inference

See [`openai.gen_ai.client.inference`](../openai/client-inference/spans/openai.gen_ai.client.inference.refinement.md) for the definition.

### Embeddings

See [common embeddings span definition](client-embeddings/spans/gen_ai.client.embeddings.md).

### Fetch response

See [`openai.fetch_response.client`](../openai/client-fetch-response/spans/openai.fetch_response.client.refinement.md) for the definition.

## Metrics

OpenAI metrics follow [Generative AI metrics](../README.md) with the noted additional attributes.
Individual systems may include additional system-specific attributes. It is recommended to check system-specific documentation, if available.

### Metric: `gen_ai.client.inference.usage.input_tokens`

Reports the usage of input tokens following the common [gen_ai.client.inference.usage.input_tokens](client-inference/metrics/gen_ai.client.inference.usage.input_tokens.md) definition.

See [`openai.gen_ai.client.inference.usage.input_tokens`](../openai/client-inference/metrics/openai.gen_ai.client.inference.usage.input_tokens.refinement.md) for the definition.

### Metric: `gen_ai.client.inference.usage.output_tokens`

Reports the usage of output tokens following the common [gen_ai.client.inference.usage.output_tokens](client-inference/metrics/gen_ai.client.inference.usage.output_tokens.md) definition.

See [`openai.gen_ai.client.inference.usage.output_tokens`](../openai/client-inference/metrics/openai.gen_ai.client.inference.usage.output_tokens.refinement.md) for the definition.

### Metric: `gen_ai.client.inference.usage.cache_read.input_tokens`

Reports the usage of cached input tokens following the common [gen_ai.client.inference.usage.cache_read.input_tokens](client-inference/metrics/gen_ai.client.inference.usage.cache_read.input_tokens.md) definition.

See [`openai.gen_ai.client.inference.usage.cache_read.input_tokens`](../openai/client-inference/metrics/openai.gen_ai.client.inference.usage.cache_read.input_tokens.refinement.md) for the definition.

### Metric: `gen_ai.client.inference.usage.cache_write.input_tokens`

Reports the usage of input tokens written to a provider-managed cache following the common [gen_ai.client.inference.usage.cache_write.input_tokens](client-inference/metrics/gen_ai.client.inference.usage.cache_write.input_tokens.md) definition.

See [`openai.gen_ai.client.inference.usage.cache_write.input_tokens`](../openai/client-inference/metrics/openai.gen_ai.client.inference.usage.cache_write.input_tokens.refinement.md) for the definition.

### Metric: `gen_ai.client.inference.usage.reasoning.output_tokens`

Reports the usage of reasoning output tokens following the common [gen_ai.client.inference.usage.reasoning.output_tokens](client-inference/metrics/gen_ai.client.inference.usage.reasoning.output_tokens.md) definition.

See [`openai.gen_ai.client.inference.usage.reasoning.output_tokens`](../openai/client-inference/metrics/openai.gen_ai.client.inference.usage.reasoning.output_tokens.refinement.md) for the definition.

### Metric: `gen_ai.client.inference.operation.input_tokens`

Reports the usage of input tokens following the common [gen_ai.client.inference.operation.input_tokens](client-inference/metrics/gen_ai.client.inference.operation.input_tokens.md) definition.

See [`openai.gen_ai.client.inference.operation.input_tokens`](../openai/client-inference/metrics/openai.gen_ai.client.inference.operation.input_tokens.refinement.md) for the definition.

### Metric: `gen_ai.client.inference.operation.output_tokens`

Reports the usage of output tokens following the common [gen_ai.client.inference.operation.output_tokens](client-inference/metrics/gen_ai.client.inference.operation.output_tokens.md) definition.

See [`openai.gen_ai.client.inference.operation.output_tokens`](../openai/client-inference/metrics/openai.gen_ai.client.inference.operation.output_tokens.refinement.md) for the definition.

### Metric: `gen_ai.client.operation.duration`

Measures the to complete an operation following the common [gen_ai.client.operation.duration](./gen-ai-metrics.md#metric-gen_aiclientoperationduration) definition.

<!-- weaver .refinements.metrics[] | select(.id == "openai.client.operation.duration") -->
<!-- NOTE: THIS TEXT IS AUTOGENERATED. DO NOT EDIT BY HAND. -->
<!-- see templates/registry/markdown/snippet.md.j2 -->
<!-- prettier-ignore-start -->

| Name | Instrument Type | Unit (UCUM) | Description | Stability | Entity Associations |
| -------- | --------------- | ----------- | -------------- | --------- | ------ |
| `gen_ai.client.operation.duration` | Histogram | `s` | OpenAI-specific extension to `gen_ai.client.operation.duration`. Adds `openai.response.service_tier` and `openai.response.system_fingerprint` when the provider is `openai`. [1] | ![Development](https://img.shields.io/badge/-development-blue) | |

**[1]:** This metric SHOULD NOT be reported for inference, embeddings, execute tool, or invoke agent client operations; use `gen_ai.client.inference.duration`, `gen_ai.client.embeddings.duration`, `gen_ai.execute_tool.duration`, or `gen_ai.client.invoke_agent.duration` instead.
This metric SHOULD NOT be reported for retrieval operations.

This metric SHOULD be specified with [ExplicitBucketBoundaries](https://github.com/open-telemetry/opentelemetry-specification/blob/v1.55.0/specification/metrics/api.md#instrument-advisory-parameters) of `[0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12, 10.24, 20.48, 40.96, 81.92]`.

**Requirement level:** [Recommended](https://github.com/open-telemetry/semantic-conventions/blob/v1.45.0/docs/general/signal-requirement-level.md).

**Attributes:**

| Key | Stability | [Requirement Level](https://opentelemetry.io/docs/specs/semconv/general/attribute-requirement-level/) | Value Type | Description | Example Values |
| --- | --- | --- | --- | --- | --- |
| [`gen_ai.operation.name`](/docs/registry/attributes/gen-ai.md) | ![Development](https://img.shields.io/badge/-development-blue) | `Required` | string | The name of the operation being performed. [1] | `chat`; `generate_content`; `realtime_inference` |
| [`error.type`](https://github.com/open-telemetry/semantic-conventions/blob/v1.45.0/docs/registry/attributes/error.md) | ![Stable](https://img.shields.io/badge/-stable-lightgreen) | `Conditionally Required` If the operation ended in an error. | string | Describes a class of error the operation ended with. [2] | `timeout`; `java.net.UnknownHostException`; `server_certificate_invalid`; `500` |
| [`gen_ai.provider.name`](/docs/registry/attributes/gen-ai.md) | ![Development](https://img.shields.io/badge/-development-blue) | `Conditionally Required` [3] | string | The Generative AI provider as identified by the client or server instrumentation. [4] | `openai`; `gcp.gen_ai`; `gcp.vertex_ai` |
| [`gen_ai.request.model`](/docs/registry/attributes/gen-ai.md) | ![Development](https://img.shields.io/badge/-development-blue) | `Conditionally Required` If available. | string | The name of the GenAI model a request is being made to. [5] | `gpt-4` |
| [`server.port`](https://github.com/open-telemetry/semantic-conventions/blob/v1.45.0/docs/registry/attributes/server.md) | ![Stable](https://img.shields.io/badge/-stable-lightgreen) | `Conditionally Required` If `server.address` is set. | int | GenAI server port. [6] | `80`; `8080`; `443` |
| [`gen_ai.response.model`](/docs/registry/attributes/gen-ai.md) | ![Development](https://img.shields.io/badge/-development-blue) | `Recommended` | string | The name of the model that generated the response. | `gpt-4-0613` |
| [`openai.response.service_tier`](/docs/registry/attributes/openai.md) | ![Development](https://img.shields.io/badge/-development-blue) | `Recommended` | string | The service tier used for the response. | `scale`; `default` |
| [`openai.response.system_fingerprint`](/docs/registry/attributes/openai.md) | ![Development](https://img.shields.io/badge/-development-blue) | `Recommended` | string | A fingerprint to track any eventual change in the Generative AI environment. | `fp_44709d6fcb` |
| [`server.address`](https://github.com/open-telemetry/semantic-conventions/blob/v1.45.0/docs/registry/attributes/server.md) | ![Stable](https://img.shields.io/badge/-stable-lightgreen) | `Recommended` | string | GenAI server address. [7] | `example.com`; `10.1.2.80`; `/tmp/my.sock` |

**[1] `gen_ai.operation.name`:** If one of the predefined values applies, but specific system uses a different name it's RECOMMENDED to document it in the semantic conventions for specific GenAI system and use system-specific name in the instrumentation. If a different name is not documented, instrumentation libraries SHOULD use applicable predefined value.

**[2] `error.type`:** The `error.type` SHOULD match the error code returned by the Generative AI provider or the client library,
the canonical name of exception that occurred, or another low-cardinality error identifier.
Instrumentations SHOULD document the list of errors they report.

**[3] `gen_ai.provider.name`:** If the operation involves a call to a GenAI provider.

**[4] `gen_ai.provider.name`:** Semantic conventions for individual GenAI operations SHOULD clarify which
kinds of providers (e.g. inference, embeddings, retrieval, memory, hosted
agent providers) apply when it is not clear from context.

The attribute SHOULD be set based on the instrumentation's best knowledge
and may differ from the actual upstream provider. For example, a client SDK
may be configured against a proxy or hosting platform that transparently
relays requests to a different provider.

The `gen_ai.provider.name` attribute acts as a discriminator that
identifies the GenAI telemetry format flavor specific to that provider
within GenAI semantic conventions.
It SHOULD be set consistently with provider-specific attributes and signals.
For example, GenAI spans, metrics, and events related to AWS Bedrock
should have the `gen_ai.provider.name` set to `aws.bedrock` and include
applicable `aws.bedrock.*` attributes and are not expected to include
`openai.*` attributes.

**[5] `gen_ai.request.model`:** The name of the GenAI model a request is being made to. If the model is supplied by a vendor, then the value must be the exact name of the model requested. If the model is a fine-tuned custom model, the value should have a more specific name than the base model that's been fine-tuned.

**[6] `server.port`:** When observed from the client side, and when communicating through an intermediary, `server.port` SHOULD represent the server port behind any intermediaries, for example proxies, if it's available.

**[7] `server.address`:** When observed from the client side, and when communicating through an intermediary, `server.address` SHOULD represent the server address behind any intermediaries, for example proxies, if it's available.

---

`error.type` has the following list of well-known values. If one of them applies, then the respective value MUST be used; otherwise, a custom value MAY be used.

| Value | Description | Stability |
| --- | --- | --- |
| `_OTHER` | A fallback error value to be used when the instrumentation doesn't define a custom value. | ![Stable](https://img.shields.io/badge/-stable-lightgreen) |

---

`gen_ai.operation.name` has the following list of well-known values. If one of them applies, then the respective value MUST be used; otherwise, a custom value MAY be used.

| Value | Description | Stability |
| --- | --- | --- |
| `chat` | Chat completion operation such as [OpenAI Chat API](https://platform.openai.com/docs/api-reference/chat) | ![Development](https://img.shields.io/badge/-development-blue) |
| `create_agent` | Create GenAI agent | ![Development](https://img.shields.io/badge/-development-blue) |
| `create_memory` | Create new memory records | ![Development](https://img.shields.io/badge/-development-blue) |
| `create_memory_store` | Create or initialize a memory store | ![Development](https://img.shields.io/badge/-development-blue) |
| `delete_memory` | Delete memory records | ![Development](https://img.shields.io/badge/-development-blue) |
| `delete_memory_store` | Delete or deprovision a memory store | ![Development](https://img.shields.io/badge/-development-blue) |
| `embeddings` | Embeddings operation such as [OpenAI Create embeddings API](https://platform.openai.com/docs/api-reference/embeddings/create) | ![Development](https://img.shields.io/badge/-development-blue) |
| `execute_tool` | Execute a tool | ![Development](https://img.shields.io/badge/-development-blue) |
| `fetch_response` | Fetch a previously generated model response by its identifier, without performing inference, such as [OpenAI Get a model response](https://platform.openai.com/docs/api-reference/responses/get) [8] | ![Development](https://img.shields.io/badge/-development-blue) |
| `generate_content` | Multimodal content generation operation such as [Gemini Generate Content](https://ai.google.dev/api/generate-content) | ![Development](https://img.shields.io/badge/-development-blue) |
| `invoke_agent` | Invoke GenAI agent | ![Development](https://img.shields.io/badge/-development-blue) |
| `invoke_runner` | Invoke a framework runner that is not itself an agent or a workflow | ![Development](https://img.shields.io/badge/-development-blue) |
| `invoke_workflow` | Invoke GenAI workflow | ![Development](https://img.shields.io/badge/-development-blue) |
| `plan` | Agent planning or task decomposition phase | ![Development](https://img.shields.io/badge/-development-blue) |
| `realtime_inference` | Server-side model generation within a realtime, bidirectional streaming session such as [OpenAI Realtime](https://platform.openai.com/docs/guides/realtime) or [Gemini Live](https://ai.google.dev/gemini-api/docs/live). | ![Development](https://img.shields.io/badge/-development-blue) |
| `retrieval` | Execution of a retrieval pipeline that returns documents relevant to a query [9] | ![Development](https://img.shields.io/badge/-development-blue) |
| `search_memory` | Search/query memories from a memory store | ![Development](https://img.shields.io/badge/-development-blue) |
| `text_completion` | Text completions operation such as [OpenAI Completions API (Legacy)](https://platform.openai.com/docs/api-reference/completions) | ![Development](https://img.shields.io/badge/-development-blue) |
| `update_memory` | Update existing memory records | ![Development](https://img.shields.io/badge/-development-blue) |
| `upsert_memory` | Create or update memory records without the caller choosing which | ![Development](https://img.shields.io/badge/-development-blue) |
| `user_speech` | Describes the process of recording user speech input. | ![Development](https://img.shields.io/badge/-development-blue) |

**[8]:** Instrumentations SHOULD NOT report token usage (as attributes or metrics) for this operation.

**[9]:** Examples include LangChain, LlamaIndex, and Haystack retrievers.
A retrieval pipeline usually combines other operations such as embeddings,
database queries, web search, or reranking. These operations SHOULD be
reported following their own conventions.

<!-- prettier-ignore-end -->
<!-- END AUTOGENERATED TEXT -->
<!-- endweaver -->

### Metric: `gen_ai.client.inference.duration`

Measures the duration to complete an inference operation following the common [gen_ai.client.inference.duration](client-inference/metrics/gen_ai.client.inference.duration.md) definition.

See [`openai.gen_ai.client.inference.duration`](../openai/client-inference/metrics/openai.gen_ai.client.inference.duration.refinement.md) for the definition.

[DocumentStatus]: https://opentelemetry.io/docs/specs/otel/document-status
