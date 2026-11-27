# Client Invoke Agent Duration Metric

> **[Semantic Convention](../../docs/gen-ai/client-invoke-agent/metrics/gen_ai.client.invoke_agent.duration.md)**

## Required

| Attribute | Supporting Libraries |
| --- | --- |
| gen_ai.operation.name | [aws-bedrock-agent], [azure-ai-foundry], [google-genai], [openai-assistants] |

## Conditionally Required

| Attribute | Supporting Libraries |
| --- | --- |
| gen_ai.agent.name | [azure-ai-foundry], [google-genai], [openai-assistants] |
| gen_ai.provider.name | [aws-bedrock-agent], [azure-ai-foundry], [google-genai], [openai-assistants] |
| server.port | [aws-bedrock-agent], [azure-ai-foundry], [google-genai], [openai-assistants] |

## Recommended

| Attribute | Supporting Libraries |
| --- | --- |
| gen_ai.request.model | [azure-ai-foundry], [openai-assistants] |
| server.address | [aws-bedrock-agent], [azure-ai-foundry], [google-genai], [openai-assistants] |

[aws-bedrock-agent]: ../scenarios/aws-bedrock-agent/scenario.py
[azure-ai-foundry]: ../scenarios/azure-ai-foundry/scenario.py
[google-genai]: ../scenarios/google-genai/scenario.py
[openai-assistants]: ../scenarios/openai-assistants/scenario.py
