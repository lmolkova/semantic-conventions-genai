<!--- Hugo front matter used to generate the website version of this page:
linkTitle: Retrieval
--->

# Semantic conventions for generative AI retrieval

**Status**: [Development][DocumentStatus]

<!-- toc -->

- [Span: `gen_ai.retrieval`](#span-gen_airetrieval)
- [Metrics](#metrics)
  - [Metric: `gen_ai.retrieval.duration`](#metric-gen_airetrievalduration)

<!-- tocstop -->

This document defines semantic conventions for retrieval operations performed
by GenAI frameworks or applications, including spans and metrics.

Examples of retrieval operations include:

- [LangChain retrievers](https://docs.langchain.com/oss/python/integrations/retrievers)
- [LlamaIndex retrievers](https://developers.llamaindex.ai/python/framework/module_guides/querying/retriever/)
- [Haystack retrievers](https://docs.haystack.deepset.ai/docs/retrievers)

## Span: `gen_ai.retrieval`

See [`gen_ai.retrieval`](spans/gen_ai.retrieval.md) for the definition.

## Metrics

### Metric: `gen_ai.retrieval.duration`

This metric SHOULD be specified with [ExplicitBucketBoundaries] of [0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12, 10.24, 20.48, 40.96, 81.92].

See [`gen_ai.retrieval.duration`](metrics/gen_ai.retrieval.duration.md) for the definition.

[DocumentStatus]: https://opentelemetry.io/docs/specs/otel/document-status
[ExplicitBucketBoundaries]: https://github.com/open-telemetry/opentelemetry-specification/blob/v1.55.0/specification/metrics/api.md#instrument-advisory-parameters
