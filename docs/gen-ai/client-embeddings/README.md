<!--- Hugo front matter used to generate the website version of this page:
linkTitle: Client Embeddings
--->

# Semantic conventions for generative AI client embeddings

**Status**: [Development][DocumentStatus]

<!-- toc -->

- [Span: `gen_ai.client.embeddings`](#span-gen_aiclientembeddings)
- [Metrics](#metrics)
  - [Metric: `gen_ai.client.embeddings.duration`](#metric-gen_aiclientembeddingsduration)
  - [Metric: `gen_ai.client.embeddings.operation.input_tokens`](#metric-gen_aiclientembeddingsoperationinput_tokens)
- [Events](#events)
  - [Event: `gen_ai.client.embeddings.exception`](#event-gen_aiclientembeddingsexception)

<!-- tocstop -->

This document defines semantic conventions for Generative AI embeddings operations,
including client spans, metrics, and events.

Examples of embeddings operations include:

- [OpenAI Create embeddings](https://platform.openai.com/docs/api-reference/embeddings/create)
- [Google Gemini Embed Content](https://ai.google.dev/api/embeddings)
- [Cohere Embed](https://docs.cohere.com/reference/embed)

## Span: `gen_ai.client.embeddings`

See [`gen_ai.client.embeddings`](spans/gen_ai.client.embeddings.md) for the definition.

## Metrics

The following metric instruments describe Generative AI embeddings operations.

### Metric: `gen_ai.client.embeddings.duration`

This metric SHOULD be specified with [ExplicitBucketBoundaries] of [0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12, 10.24, 20.48, 40.96, 81.92].

See [`gen_ai.client.embeddings.duration`](metrics/gen_ai.client.embeddings.duration.md) for the definition.

### Metric: `gen_ai.client.embeddings.operation.input_tokens`

This metric SHOULD be specified with [ExplicitBucketBoundaries] of [1, 4, 16, 64, 256, 1024, 4096, 16384, 65536, 262144, 1048576, 4194304, 16777216, 67108864].

See [`gen_ai.client.embeddings.operation.input_tokens`](metrics/gen_ai.client.embeddings.operation.input_tokens.md) for the definition.

## Events

### Event: `gen_ai.client.embeddings.exception`

See [`gen_ai.client.embeddings.exception`](events/gen_ai.client.embeddings.exception.md) for the definition.

[DocumentStatus]: https://opentelemetry.io/docs/specs/otel/document-status
[ExplicitBucketBoundaries]: https://github.com/open-telemetry/opentelemetry-specification/blob/v1.55.0/specification/metrics/api.md#instrument-advisory-parameters
