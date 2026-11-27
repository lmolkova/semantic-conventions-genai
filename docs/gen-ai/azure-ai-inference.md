<!--- Hugo front matter used to generate the website version of this page:
linkTitle: Azure AI Inference
--->

# Semantic conventions for Azure AI Inference client operations

**Status**: [Development][DocumentStatus]

<!-- toc -->

- [Spans](#spans)
  - [Inference](#inference)
  - [Embedding](#embedding)
- [Metrics](#metrics)

<!-- tocstop -->

The Semantic Conventions for [Azure AI Inference](https://learn.microsoft.com/azure/ai-studio) extend and override the [GenAI Semantic Conventions](README.md).

## Spans

### Inference

`gen_ai.provider.name` MUST be set to `"azure.ai.inference"` and SHOULD be provided **at span creation time**.

See [`azure.ai.gen_ai.client.inference`](../azure/client-inference/spans/azure.ai.gen_ai.client.inference.md) for the definition.

### Embedding

See [common embedding span definition](client-embeddings/spans/gen_ai.client.embeddings.md).

## Metrics

Azure AI Inference metrics follow generic [Generative AI metrics](gen-ai-metrics.md).

[DocumentStatus]: https://opentelemetry.io/docs/specs/otel/document-status
