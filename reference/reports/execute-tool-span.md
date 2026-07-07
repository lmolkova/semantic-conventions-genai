# Execute Tool Span

> **[Semantic Convention](../../docs/gen-ai/gen-ai-spans.md#execute-tool-span)**

## Required

| Attribute | Supporting Libraries |
| --- | --- |
| gen_ai.operation.name | [a2a], [agent-framework], [autogen], [crewai], [google-adk], [groq], [instructor], [litellm], [llamaindex], [mistralai], [openai], [openai-agents], [openai-assistants], [pydantic-ai] |
| gen_ai.tool.name | [a2a], [agent-framework], [autogen], [crewai], [google-adk], [groq], [instructor], [litellm], [llamaindex], [mistralai], [openai], [openai-agents], [openai-assistants], [pydantic-ai] |

## Conditionally Required

| Attribute | Supporting Libraries |
| --- | --- |
| gen_ai.agent.name | [google-adk], [openai-agents], [pydantic-ai] |

## Recommended

| Attribute | Supporting Libraries |
| --- | --- |
| gen_ai.tool.call.id | [a2a], [agent-framework], [autogen], [google-adk], [groq], [instructor], [litellm], [llamaindex], [mistralai], [openai], [openai-agents], [openai-assistants], [pydantic-ai] |
| gen_ai.tool.description | [agent-framework], [autogen], [crewai], [google-adk], [groq], [instructor], [litellm], [llamaindex], [mistralai], [openai], [openai-agents], [openai-assistants], [pydantic-ai] |
| gen_ai.tool.type | [a2a], [agent-framework], [autogen], [crewai], [google-adk], [groq], [instructor], [litellm], [llamaindex], [mistralai], [openai], [openai-agents], [openai-assistants], [pydantic-ai] |

## Opt-In

| Attribute | Supporting Libraries |
| --- | --- |
| gen_ai.tool.call.arguments | [a2a], [agent-framework], [autogen], [crewai], [google-adk], [groq], [instructor], [litellm], [llamaindex], [mistralai], [openai], [openai-agents], [openai-assistants], [pydantic-ai] |
| gen_ai.tool.call.result | [a2a], [agent-framework], [autogen], [crewai], [google-adk], [groq], [instructor], [litellm], [llamaindex], [mistralai], [openai], [openai-agents], [openai-assistants], [pydantic-ai] |

[a2a]: ../scenarios/a2a/scenario.py
[agent-framework]: ../scenarios/agent-framework/scenario.py
[autogen]: ../scenarios/autogen/scenario.py
[crewai]: ../scenarios/crewai/scenario.py
[google-adk]: ../scenarios/google-adk/scenario.py
[groq]: ../scenarios/groq/scenario.py
[instructor]: ../scenarios/instructor/scenario.py
[litellm]: ../scenarios/litellm/scenario.py
[llamaindex]: ../scenarios/llamaindex/scenario.py
[mistralai]: ../scenarios/mistralai/scenario.py
[openai]: ../scenarios/openai/scenario.py
[openai-agents]: ../scenarios/openai-agents/scenario.py
[openai-assistants]: ../scenarios/openai-assistants/scenario.py
[pydantic-ai]: ../scenarios/pydantic-ai/scenario.py
