<!--- Hugo front matter used to generate the website version of this page:
linkTitle: Client Inference
--->

# Semantic conventions for generative AI client inference

**Status**: [Development][DocumentStatus]

<!-- toc -->

- [Span: `gen_ai.client.inference`](#span-gen_aiclientinference)
- [Metrics](#metrics)
  - [Metric: `gen_ai.client.inference.duration`](#metric-gen_aiclientinferenceduration)
  - [Metric: `gen_ai.client.inference.time_to_first_chunk`](#metric-gen_aiclientinferencetime_to_first_chunk)
  - [Metric: `gen_ai.client.inference.time_per_output_chunk`](#metric-gen_aiclientinferencetime_per_output_chunk)
  - [Metric: `gen_ai.client.inference.usage.input_tokens`](#metric-gen_aiclientinferenceusageinput_tokens)
  - [Metric: `gen_ai.client.inference.usage.output_tokens`](#metric-gen_aiclientinferenceusageoutput_tokens)
  - [Metric: `gen_ai.client.inference.usage.cache_read.input_tokens`](#metric-gen_aiclientinferenceusagecache_readinput_tokens)
  - [Metric: `gen_ai.client.inference.usage.cache_write.input_tokens`](#metric-gen_aiclientinferenceusagecache_writeinput_tokens)
  - [Metric: `gen_ai.client.inference.usage.reasoning.output_tokens`](#metric-gen_aiclientinferenceusagereasoningoutput_tokens)
  - [Metric: `gen_ai.client.inference.operation.input_tokens`](#metric-gen_aiclientinferenceoperationinput_tokens)
  - [Metric: `gen_ai.client.inference.operation.output_tokens`](#metric-gen_aiclientinferenceoperationoutput_tokens)
- [Events](#events)
  - [Event: `gen_ai.client.inference.operation.details`](#event-gen_aiclientinferenceoperationdetails)
  - [Event: `gen_ai.client.inference.exception`](#event-gen_aiclientinferenceexception)

<!-- tocstop -->

This document defines semantic conventions for Generative AI inference operations,
including client spans, events, and metrics.

Examples of inference operations include:

- [OpenAI Create Response](https://platform.openai.com/docs/api-reference/responses/create)
- [OpenAI Create Chat Completion](https://platform.openai.com/docs/api-reference/chat/create)
- [Anthropic Create a Message](https://docs.anthropic.com/en/api/messages)
- [Google Gemini Create Interaction](https://ai.google.dev/gemini-api/docs/interactions-overview)
- [Google Gemini Generate Content](https://ai.google.dev/api/generate-content)

including their streaming and non-streaming variants.

## Span: `gen_ai.client.inference`

See [`gen_ai.client.inference`](spans/gen_ai.client.inference.md) for the definition.

For conventions on capturing instructions, inputs, and outputs on inference spans,
see [Capturing instructions, inputs, and outputs](../gen-ai-spans.md#capturing-instructions-inputs-and-outputs).

## Metrics

The following metric instruments describe Generative AI inference operations.

Inference token metrics (`gen_ai.client.inference.usage.*` counters and
`gen_ai.client.inference.operation.*` histograms) are defined in
[Inference Token Metrics](../gen-ai-token-metrics.md).

### Metric: `gen_ai.client.inference.duration`

This metric SHOULD be specified with [ExplicitBucketBoundaries] of [0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12, 10.24, 20.48, 40.96, 81.92].

See [`gen_ai.client.inference.duration`](metrics/gen_ai.client.inference.duration.md) for the definition.

### Metric: `gen_ai.client.inference.time_to_first_chunk`

This metric SHOULD be specified with [ExplicitBucketBoundaries] of [0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12, 10.24, 20.48, 40.96, 81.92].

See [`gen_ai.client.inference.time_to_first_chunk`](metrics/gen_ai.client.inference.time_to_first_chunk.md) for the definition.

### Metric: `gen_ai.client.inference.time_per_output_chunk`

This metric SHOULD be specified with [ExplicitBucketBoundaries] of [0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12, 10.24, 20.48, 40.96, 81.92].

See [`gen_ai.client.inference.time_per_output_chunk`](metrics/gen_ai.client.inference.time_per_output_chunk.md) for the definition.

### Metric: `gen_ai.client.inference.usage.input_tokens`

See [Inference Token Metrics](../gen-ai-token-metrics.md#metric-gen_aiclientinferenceusageinput_tokens).

### Metric: `gen_ai.client.inference.usage.output_tokens`

See [Inference Token Metrics](../gen-ai-token-metrics.md#metric-gen_aiclientinferenceusageoutput_tokens).

### Metric: `gen_ai.client.inference.usage.cache_read.input_tokens`

See [Inference Token Metrics](../gen-ai-token-metrics.md#metric-gen_aiclientinferenceusagecache_readinput_tokens).

### Metric: `gen_ai.client.inference.usage.cache_write.input_tokens`

See [Inference Token Metrics](../gen-ai-token-metrics.md#metric-gen_aiclientinferenceusagecache_writeinput_tokens).

### Metric: `gen_ai.client.inference.usage.reasoning.output_tokens`

See [Inference Token Metrics](../gen-ai-token-metrics.md#metric-gen_aiclientinferenceusagereasoningoutput_tokens).

### Metric: `gen_ai.client.inference.operation.input_tokens`

See [Inference Token Metrics](../gen-ai-token-metrics.md#metric-gen_aiclientinferenceoperationinput_tokens).

### Metric: `gen_ai.client.inference.operation.output_tokens`

See [Inference Token Metrics](../gen-ai-token-metrics.md#metric-gen_aiclientinferenceoperationoutput_tokens).

## Events

> [!Note]
> Events are in-development and not yet available in some languages. Check [spec-compliance matrix](https://github.com/open-telemetry/opentelemetry-specification/blob/v1.55.0/spec-compliance-matrix.md#logs) to see the implementation status in corresponding language.

### Event: `gen_ai.client.inference.operation.details`

See [`gen_ai.client.inference.operation.details`](events/gen_ai.client.inference.operation.details.md) for the definition.

### Event: `gen_ai.client.inference.exception`

See [`gen_ai.client.inference.exception`](events/gen_ai.client.inference.exception.md) for the definition.

[DocumentStatus]: https://opentelemetry.io/docs/specs/otel/document-status
[ExplicitBucketBoundaries]: https://github.com/open-telemetry/opentelemetry-specification/blob/v1.55.0/specification/metrics/api.md#instrument-advisory-parameters
