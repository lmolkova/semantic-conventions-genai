# Design choices behind usage metrics

TODO link to the doc

**Why is the modality breakdown on the counters and not on the histograms?
Why do we need two sets of metrics?**

Imagine a single histogram, `gen_ai.imaginary.inference.input_tokens`, with
modality as a dimension. Each inference call would record one measurement per
modality in its input.

What could it answer?

- **Distribution of tokens per modality** - precisely, if grouped by modality.
- **Total tokens per modality** - also yes: the histogram's sum series does
  everything the counters do.
- **Distribution of input tokens per call** - no. The p95 of the image parts
  plus the p95 of the text parts is not the p95 of a call.

The problem is that the query for the third question looks perfectly valid:

```promql
histogram_quantile(0.95,
  sum(rate({"gen_ai.imaginary.inference.input_tokens"}[5m]))
)
```

Take a workload of 100 identical calls, each with 100 text and 200 image input
tokens. Every call has an input of 300 tokens, but the histogram holds 200
measurements - one hundred of `100` and one hundred of `200`:

| | Value |
| --- | --- |
| p95 the query returns | 200 |
| p95 of the actual input size | 300 |

The p95 is a number no call ever had, and it is lower than the smallest real
input. 

Modality could instead be part of the metric name -
`gen_ai.imaginary.inference.text.input_tokens` and so on. Each such histogram
records at most one measurement per call, so each is well-formed on its own. One 
instrument per modality per category multiplies quickly, and histograms cost
far more than counters, so this suits advanced needs. The `gen_ai.client.inference.input_tokens` and TODO output tokens
broken down by modality don't have this usability concern specific to histograms 
and also they satisfy basic need of cost approximation and ratio between modalities
at much lover telemetry volume.

**Why does `gen_ai.token.modality` have an `unknown` value?**

So that summing a counter across `gen_ai.token.modality` always equals its
total, even against providers that report no modality breakdown.

The counters are aggregatable only because each token lands in exactly one
modality bucket, and `gen_ai.token.modality` is required on all of them. A
provider that reports no breakdown still has to put its tokens somewhere, and
without `unknown` both options are wrong: omitting the attribute makes the sum
inconsistent with providers that set it, and guessing `text` reports a modality
nobody observed.

`unknown` means "this producer had no modality information", not "this token had
no modality" - it is the bucket that keeps the partition complete.

[Exemplars]: https://opentelemetry.io/docs/specs/otel/metrics/data-model/#exemplars
