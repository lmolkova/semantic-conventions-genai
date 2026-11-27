<!--- Hugo front matter used to generate the website version of this page:
linkTitle: Token Metrics
--->

# Semantic conventions for generative AI inference token metrics

**Status**: [Development][DocumentStatus]

<!-- toc -->

- [Semantic conventions for generative AI inference token metrics](#semantic-conventions-for-generative-ai-inference-token-metrics)
  - [How to aggregate token usage](#how-to-aggregate-token-usage)
  - [Inference token metrics](#inference-token-metrics)
    - [Metric: `gen_ai.client.inference.usage.input_tokens`](#metric-gen_aiclientinferenceusageinput_tokens)
    - [Metric: `gen_ai.client.inference.usage.output_tokens`](#metric-gen_aiclientinferenceusageoutput_tokens)
    - [Metric: `gen_ai.client.inference.usage.cache_read.input_tokens`](#metric-gen_aiclientinferenceusagecache_readinput_tokens)
    - [Metric: `gen_ai.client.inference.usage.cache_write.input_tokens`](#metric-gen_aiclientinferenceusagecache_writeinput_tokens)
    - [Metric: `gen_ai.client.inference.usage.reasoning.output_tokens`](#metric-gen_aiclientinferenceusagereasoningoutput_tokens)
    - [Metric: `gen_ai.client.inference.operation.input_tokens`](#metric-gen_aiclientinferenceoperationinput_tokens)
    - [Metric: `gen_ai.client.inference.operation.output_tokens`](#metric-gen_aiclientinferenceoperationoutput_tokens)
<!-- tocstop -->

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

The conventions described in this document are specific to Generative AI client
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

### Metric: `gen_ai.client.inference.usage.input_tokens`

See [`gen_ai.client.inference.usage.input_tokens`](client-inference/metrics/gen_ai.client.inference.usage.input_tokens.md) for the definition.

### Metric: `gen_ai.client.inference.usage.output_tokens`

See [`gen_ai.client.inference.usage.output_tokens`](client-inference/metrics/gen_ai.client.inference.usage.output_tokens.md) for the definition.

### Metric: `gen_ai.client.inference.usage.cache_read.input_tokens`

See [`gen_ai.client.inference.usage.cache_read.input_tokens`](client-inference/metrics/gen_ai.client.inference.usage.cache_read.input_tokens.md) for the definition.

### Metric: `gen_ai.client.inference.usage.cache_write.input_tokens`

See [`gen_ai.client.inference.usage.cache_write.input_tokens`](client-inference/metrics/gen_ai.client.inference.usage.cache_write.input_tokens.md) for the definition.

### Metric: `gen_ai.client.inference.usage.reasoning.output_tokens`

See [`gen_ai.client.inference.usage.reasoning.output_tokens`](client-inference/metrics/gen_ai.client.inference.usage.reasoning.output_tokens.md) for the definition.

### Metric: `gen_ai.client.inference.operation.input_tokens`

See [`gen_ai.client.inference.operation.input_tokens`](client-inference/metrics/gen_ai.client.inference.operation.input_tokens.md) for the definition.

### Metric: `gen_ai.client.inference.operation.output_tokens`


See [`gen_ai.client.inference.operation.output_tokens`](client-inference/metrics/gen_ai.client.inference.operation.output_tokens.md) for the definition.

[DocumentStatus]: https://opentelemetry.io/docs/specs/otel/document-status
