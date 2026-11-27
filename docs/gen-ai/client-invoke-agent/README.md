<!--- Hugo front matter used to generate the website version of this page:
linkTitle: Client Agent Invocations
--->

# Semantic conventions for generative AI client agent invocations

**Status**: [Development][DocumentStatus]

<!-- toc -->

- [Spans](#spans)
  - [Span: `gen_ai.client.invoke_agent`](#span-gen_aiclientinvoke_agent)
- [Metrics](#metrics)
  - [Metric: `gen_ai.client.invoke_agent.duration`](#metric-gen_aiclientinvoke_agentduration)
- [Events](#events)
  - [Event: `gen_ai.client.invoke_agent.exception`](#event-gen_aiclientinvoke_agentexception)

<!-- tocstop -->

This document defines semantic conventions for invoking GenAI agents
hosted by a remote agent service, including client spans, metrics, and events.

Examples of remote agent invocations include:

- [OpenAI Assistants](https://platform.openai.com/docs/api-reference/assistants)
- [Azure AI Foundry Agents](https://learn.microsoft.com/azure/ai-foundry/agents/overview)
- [AWS Bedrock Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)

In-process agent invocations are covered by the
[invoke agent internal span](../gen-ai-agent-spans.md#invoke-agent-internal-span).
Agent creation is covered by the
[create agent span](../gen-ai-agent-spans.md#create-agent-span).

## Spans

### Span: `gen_ai.client.invoke_agent`

See [`gen_ai.client.invoke_agent`](spans/gen_ai.client.invoke_agent.md) for the definition.

## Metrics

The following metric instruments describe remote agent invocations.

### Metric: `gen_ai.client.invoke_agent.duration`

This metric SHOULD be specified with [ExplicitBucketBoundaries] of [0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12, 10.24, 20.48, 40.96, 81.92].

See [`gen_ai.client.invoke_agent.duration`](metrics/gen_ai.client.invoke_agent.duration.md) for the definition.

## Events

### Event: `gen_ai.client.invoke_agent.exception`

See [`gen_ai.client.invoke_agent.exception`](events/gen_ai.client.invoke_agent.exception.md) for the definition.

[DocumentStatus]: https://opentelemetry.io/docs/specs/otel/document-status
