# Client Operation Duration Metric

> **[Semantic Convention](../../docs/gen-ai/registry/metrics/gen_ai.client.operation.duration.md)**

## Required

| Attribute | Supporting Libraries |
| --- | --- |
| gen_ai.operation.name | [adk_a2a] |

## Conditionally Required

| Attribute | Supporting Libraries |
| --- | --- |
| gen_ai.provider.name | [adk_a2a] |
| gen_ai.request.model | [adk_a2a] |
| server.port | (none) |

## Recommended

| Attribute | Supporting Libraries |
| --- | --- |
| gen_ai.response.model | [adk_a2a] |
| server.address | (none) |

[adk_a2a]: ../scenarios/adk_a2a/scenario.py
