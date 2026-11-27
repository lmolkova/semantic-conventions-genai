<!--- Hugo front matter used to generate the website version of this page:
linkTitle: Agent2Agent Protocol
--->

# Semantic conventions for Agent2Agent Protocol (A2A)

**Status**: [Development][DocumentStatus]

<!-- toc -->

- [Spans](#spans)
  - [Client](#client)
  - [Server](#server)
    - [Server over HTTP](#server-over-http)
    - [Server over gRPC](#server-over-grpc)
- [Trace examples](#trace-examples)
  - [Agent invocation](#agent-invocation)
  - [Asynchronous task polling](#asynchronous-task-polling)
  - [Server processing](#server-processing)

<!-- tocstop -->

[Agent2Agent Protocol](https://a2a-protocol.org/latest/specification/) (A2A)
enables agents to communicate across vendors and frameworks.

A2A conventions describe the logical A2A request, method, task lifecycle,
tenant routing, A2A
[`contextId`](https://a2a-protocol.org/latest/specification/#341-context-identifier-semantics)
correlation, and streaming response behavior.

## Spans

### Client

See [`a2a.client`](client/spans/a2a.client.md) for the definition.

### Server

See [`a2a.server`](server/spans/a2a.server.md) for the definition.

#### Server over HTTP

See [`a2a.http.server`](server/spans/a2a.http.server.md) for the definition.

#### Server over gRPC

See [`a2a.grpc.server`](server/spans/a2a.grpc.server.md) for the definition.

## Trace examples

The examples below show the spans that can be captured when instrumentation is
enabled at the agent, A2A, and transport layers. An A2A instrumentation reports
only the A2A spans; an agent framework reports `gen_ai.client.invoke_agent`
when applicable.

### Agent invocation

When an agent framework invokes a remote agent and its context remains active,
the A2A span can be a child of `gen_ai.client.invoke_agent`:

```text
invoke_agent weather-agent         (GenAI agent)
└─ SendMessage                     (A2A client)
   └─ POST /message:send           (HTTP client)
```

For RPC bindings, the innermost span is RPC Client
`A2AService.SendMessage` rather than an HTTP client span.

### Asynchronous task polling

When the client sends a message without waiting for task completion, it can
poll the task. While the parent context remains active, the A2A operation spans
are siblings; `GetTask` is not a child of `SendMessage`:

```text
invoke_agent weather-agent         (GenAI agent)
├─ SendMessage                     (A2A client)
│  └─ POST /message:send           (HTTP client)
├─ GetTask                         (A2A client)
│  └─ GET /tasks/{id}              (HTTP client)
└─ GetTask                         (A2A client)
   └─ GET /tasks/{id}              (HTTP client)
```

If polling occurs later or in a different process without the original parent
context, the polling operations are separate traces. `a2a.task.id` provides
the operational correlation between the operations.

### Server processing

On the receiving side, when instrumentation can detect the transport server
span, it SHOULD enrich that span with A2A attributes. For HTTP, it SHOULD also
rename the span to the A2A method name:

```text
SendMessage                        (HTTP server enriched with A2A attributes)
```

For gRPC, instrumentation SHOULD preserve the transport span name:

```text
A2AService.SendMessage             (gRPC server enriched with A2A attributes)
```

When instrumentation cannot detect a transport server span, it reports a
standalone A2A server span:

```text
SendMessage                        (standalone A2A server)
```

[DocumentStatus]: https://opentelemetry.io/docs/specs/otel/document-status
