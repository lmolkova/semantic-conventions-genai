# Client Inference Reasoning Output Tokens Metric

> **[Semantic Convention](../../docs/gen-ai/registry/metrics/gen_ai.client.inference.usage.reasoning.output_tokens.md)**

## Required

| Attribute | Supporting Libraries |
| --- | --- |
| gen_ai.operation.name | [google-genai], [openai] |
| gen_ai.provider.name | [google-genai], [openai] |

## Conditionally Required

| Attribute | Supporting Libraries |
| --- | --- |
| gen_ai.request.model | [google-genai], [openai] |
| server.port | [openai] |

## Recommended

| Attribute | Supporting Libraries |
| --- | --- |
| gen_ai.response.model | [google-genai], [openai] |
| server.address | [openai] |

[google-genai]: ../scenarios/google-genai/scenario.py
[openai]: ../scenarios/openai/scenario.py
