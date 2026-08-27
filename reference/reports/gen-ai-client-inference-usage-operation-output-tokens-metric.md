# Client Inference Operation Output Tokens Metric

> **[Semantic Convention](../../docs/gen-ai/gen-ai-inference-usage-metrics.md#metric-gen_aiclientinferenceusageoperationoutput_tokens)**

## Required

| Attribute | Supporting Libraries |
| --- | --- |
| gen_ai.operation.name | [openai] |
| gen_ai.provider.name | [openai] |

## Conditionally Required

| Attribute | Supporting Libraries |
| --- | --- |
| gen_ai.request.model | [openai] |
| server.port | [openai] |

## Recommended

| Attribute | Supporting Libraries |
| --- | --- |
| gen_ai.response.model | [openai] |
| server.address | [openai] |

[openai]: ../scenarios/openai/scenario.py
