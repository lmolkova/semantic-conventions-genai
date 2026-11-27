<!--- Hugo front matter used to generate the website version of this page:
linkTitle: Execute Tool
--->

# Semantic conventions for generative AI tool execution

**Status**: [Development][DocumentStatus]

<!-- toc -->

- [Span: `gen_ai.execute_tool`](#span-gen_aiexecute_tool)
- [Specialized tool call spans](#specialized-tool-call-spans)
  - [Agent as a tool](#agent-as-a-tool)
  - [Agent skills](#agent-skills)
    - [Load skill span](#load-skill-span)
    - [Read skill resource span](#read-skill-resource-span)
  - [Command execution span](#command-execution-span)
- [Events](#events)
  - [Event: `gen_ai.execute_tool.exception`](#event-gen_aiexecute_toolexception)
- [Metrics](#metrics)
  - [Metric: `gen_ai.execute_tool.duration`](#metric-gen_aiexecute_toolduration)

<!-- tocstop -->

This document defines semantic conventions for tool executions performed by
GenAI agents, frameworks, or applications, including spans, events, and metrics.

## Span: `gen_ai.execute_tool`

See [`gen_ai.execute_tool`](spans/gen_ai.execute_tool.md) for the definition.

## Specialized tool call spans

When the library API or state identifies a specialized tool call,
instrumentation SHOULD refine the [execute tool span](#span-gen_aiexecute_tool)
as described below.

### Agent as a tool

See [`gen_ai.execute_tool.transfer`](spans/gen_ai.execute_tool.transfer.md) for the definition.

### Agent skills

An [Agent Skill](https://agentskills.io) is a folder holding a `SKILL.md` file -
metadata (`name`, `description`) plus instructions - and, optionally, bundled
`references/`, `assets/`, and `scripts/`. When a tool is used to interact with a
skill, instrumentations SHOULD refine
the [execute tool span](#span-gen_aiexecute_tool) as described
below.

#### Load skill span

See [`gen_ai.execute_tool.load_skill`](spans/gen_ai.execute_tool.load_skill.md) for the definition.

#### Read skill resource span

See [`gen_ai.execute_tool.read_skill_resource`](spans/gen_ai.execute_tool.read_skill_resource.md) for the definition.

### Command execution span

See [`gen_ai.execute_tool.command`](spans/gen_ai.execute_tool.command.md) for the definition.

## Events

### Event: `gen_ai.execute_tool.exception`

See [`gen_ai.execute_tool.exception`](events/gen_ai.execute_tool.exception.md) for the definition.

## Metrics

### Metric: `gen_ai.execute_tool.duration`

This metric SHOULD be specified with [ExplicitBucketBoundaries] of [0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28, 2.56, 5.12, 10.24, 20.48, 40.96, 81.92].

See [`gen_ai.execute_tool.duration`](metrics/gen_ai.execute_tool.duration.md) for the definition.

[DocumentStatus]: https://opentelemetry.io/docs/specs/otel/document-status
[ExplicitBucketBoundaries]: https://github.com/open-telemetry/opentelemetry-specification/blob/v1.55.0/specification/metrics/api.md#instrument-advisory-parameters
