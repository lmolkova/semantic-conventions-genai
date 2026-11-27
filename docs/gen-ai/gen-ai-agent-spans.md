<!--- Hugo front matter used to generate the website version of this page:
linkTitle: Agent spans
--->

# Semantic Conventions for GenAI agent and framework spans

**Status**: [Development][DocumentStatus]

<!-- toc -->

- [Semantic Conventions for GenAI agent and framework spans](#semantic-conventions-for-genai-agent-and-framework-spans)
  - [Spans](#spans)
    - [Create agent span](#create-agent-span)
    - [Invoke agent client span](#invoke-agent-client-span)
    - [Invoke agent internal span](#invoke-agent-internal-span)
      - [Event: `gen_ai.invoke_agent.exception`](#event-gen_aiinvoke_agentexception)
    - [Plan span](#plan-span)
  - [Execute tool span](#execute-tool-span)

<!-- tocstop -->

Generative AI models can be trained to use tools to access real-time information or suggest a real-world action. For example, a model can leverage a database retrieval tool to access specific information, like a customer's purchase history, so it can generate tailored shopping recommendations. Alternatively, based on a user's query, a model can make various API calls to send an email response to a colleague or complete a financial transaction on your behalf. To do so, the model must not only have access to a set of external tools, it needs the ability to plan and execute any task in a self-directed fashion. This combination of reasoning, logic, and access to external information that are all connected to a Generative AI model invokes the concept of an agent.

This document defines semantic conventions for GenAI agent and framework operations across both remote services and local frameworks.

The semantic conventions for GenAI agents extend and override the semantic conventions for [Gen AI Spans](README.md).

Check out [agent call examples](non-normative/examples-agent-calls.md).

## Spans

### Create agent span

See [`gen_ai.create_agent.client`](client-create-agent/spans/gen_ai.create_agent.client.md) for the definition.

### Invoke agent client span

Invoke agent client span, event, and metric conventions are defined in [Client Agent Invocations](client-invoke-agent/README.md).

### Invoke agent internal span

See [`gen_ai.invoke_agent.internal`](invoke-agent/spans/gen_ai.invoke_agent.internal.md) for the definition.

#### Event: `gen_ai.invoke_agent.exception`

See [`gen_ai.invoke_agent.exception`](invoke-agent/events/gen_ai.invoke_agent.exception.md) for the definition.

### Plan span

See [`gen_ai.plan.internal`](plan/spans/gen_ai.plan.internal.md) for the definition.

## Execute tool span

Execute tool span, event, and metric conventions, including specialized tool call spans such as
agents as tools and Agent Skills, are defined in [Execute Tool](execute-tool/README.md).

[DocumentStatus]: https://opentelemetry.io/docs/specs/otel/document-status
