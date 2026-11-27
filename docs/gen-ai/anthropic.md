<!--- Hugo front matter used to generate the website version of this page:
linkTitle: Anthropic
--->

# Semantic conventions for Anthropic client operations

**Status**: [Development][DocumentStatus]

<!-- toc -->

- [Spans](#spans)
  - [Inference](#inference)
  - [Embedding](#embedding)
- [Metrics](#metrics)

<!-- tocstop -->

The Semantic Conventions for [Anthropic](https://www.anthropic.com/) extend and override the [GenAI Semantic Conventions](../README.md).

## Spans

### Inference

`gen_ai.provider.name` MUST be set to `"anthropic"` and SHOULD be provided **at span creation time**.

See [`anthropic.gen_ai.client.inference`](../anthropic/client-inference/spans/anthropic.gen_ai.client.inference.md) for the definition.

### Embedding

See [common embedding span definition](client-embeddings/spans/gen_ai.client.embeddings.md).

## Metrics

Anthropic metrics follow generic [Generative AI metrics](../README.md).

[DocumentStatus]: https://opentelemetry.io/docs/specs/otel/document-status
