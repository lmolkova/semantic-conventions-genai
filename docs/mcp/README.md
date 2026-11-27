<!--- Hugo front matter used to generate the website version of this page:
linkTitle: Model Context Protocol
--->

# Semantic conventions for Model Context Protocol (MCP)

**Status**: [Development][DocumentStatus]

[Model Context Protocol](https://github.com/modelcontextprotocol/modelcontextprotocol) (MCP) is based on JSON RPC.

When instrumenting MCP calls, it's RECOMMENDED to follow MCP conventions instead of [RPC semantic conventions](https://github.com/open-telemetry/semantic-conventions/blob/v1.45.0/docs/rpc/README.md)
since MCP spans and metrics provide domain-specific context and record details
that are not covered by the RPC conventions such as message exchanges within streaming calls.

HTTP conventions (when HTTP is used as transport) do not adequately cover MCP requests
and notifications either, given that multiple MCP requests could be sent over a single
HTTP request in the corresponding request and response streams.

## Attributes

See [MCP attributes](registry/README.md#attributes).

## Operations

* [MCP client](client.md)
* [MCP server](server.md)

## Context propagation

Model Context Protocol works on top of JSON-RPC. MCP is transport independent
and works across different transports. The specification expects clients to
implement at least stdio or Streamable HTTP.

HTTP trace context propagation only covers the HTTP request, but not the individual
messages client and server exchange within the request/response streams.

Instrumentations SHOULD propagate context using the configured
[OpenTelemetry propagators](https://opentelemetry.io/docs/specs/otel/context/api-propagators/)
by injecting it into the MCP request
[`params._meta`](https://modelcontextprotocol.io/specification/2025-11-25/basic#_meta)
property bag when creating a request or notification. The receiver extracts the
context from `params._meta` and uses it as the remote parent.

Although the MCP convention expects keys in `params._meta` to be DNS-prefixed,
the context propagation keys SHOULD be written unprefixed.
[SEP-414](https://modelcontextprotocol.io/community/seps/414-request-meta)
defines this explicit handling for the W3C Trace Context and Baggage keys
(`traceparent`, `tracestate`, and `baggage`).

Here's an example of a tool call request with injected
[W3C Trace Context](https://www.w3.org/TR/trace-context/).

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get-weather",
    "_meta": {
      "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
      "tracestate": "rojo=00f067aa0ba902b7,congo=t61rcWkgMzE"
    }
  },
  "id": 1
}
```

If the application also uses [W3C Baggage](https://www.w3.org/TR/baggage/),
propagate `baggage` in the same `params._meta` property bag, as in the following
example:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get-weather",
    "_meta": {
      "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
      "baggage": "userId=alice,serverNode=DF%2028,isProduction=false"
    }
  },
  "id": 1
}
```

MCP server instrumentation SHOULD, by default, use context extracted from MCP
`params._meta` as a parent for MCP server span and SHOULD link current ambient
context, if it's present.

> [!NOTE]
> MCP and underlying transport (such as HTTP) contexts are independent. One MCP
> request can be served by multiple HTTP requests (for example, because of retries)
> and one streamable HTTP request can serve more than one MCP request/notification.
> The MCP client span becomes a parent of the MCP server span regardless of transport used;
> span links allow recording the transport context (if present).

[DocumentStatus]: https://opentelemetry.io/docs/specs/otel/document-status

## Recording MCP transport

The following table shows how to capture MCP transport and can be used be telemetry
consumers to deduce transport type.

| MCP transport      | `network.transport` attribute          | `network.protocol.*` attributes                                             | `mcp.protocol.version` attribute | Comments                                                         |
| :----------------- | :------------------------------------- | :-------------------------------------------------------------------------- | :------------------------------- | :--------------------------------------------------------------- |
| stdio              | `pipe`                                 |                                                                             | any                              |                                                                  |
| Streamable HTTP    | `tcp` (or `quic`)                      | `network.protocol.name = http` <br> `network.protocol.version = 2`          | `2025-06-18` or newer            | `mcp.protocol.version` distinguishes streamable HTTP from SSE    |
| HTTP with SSE      | `tcp` (or `quic`)                      | `network.protocol.name = http` <br> `network.protocol.version = 1.1` (or 2) | `2024-11-05` or older            | `mcp.protocol.version` distinguishes streamable HTTP from SSE    |
| Custom: websockets | `tcp` (or another applicable protocol) | `network.protocol.name = websocket`                                         | any                              |                                                                  |
| Custom: gRPC       | `tcp` (or another applicable protocol) | `network.protocol.name = http` <br> `network.protocol.version = 2`          | any                              | See [gRPC conventions](https://github.com/open-telemetry/semantic-conventions/blob/v1.45.0/docs/rpc/grpc.md) for additional details |

Note: Applications may enable instrumentation for the underlying application protocol
like HTTP (when applicable) alongside MCP instrumentation to capture additional
transport-level details, such as transport-specific error codes.

## Examples

In these examples, we assume that GenAI framework is configured to use MCP tools,
and that tool calls are handled manually, so that GenAI framework does not
instrument corresponding tool calls.

### Stdio transport

#### Initialize

```
initialize (CLIENT, trace=t1, span=s1)                     # MCP client
|
-- initialize - (SERVER, trace=t1, span=s2, parent=s1)     # MCP server
```

MCP client span (`s1`):

| Property                         | Value                                |
| :------------------------------- | :----------------------------------- |
| Span name                        | `"initialize"`                       |
| Span kind                        | `CLIENT`                             |
| Span status                      | `UNSET`                              |
| Attribute `jsonrpc.request.id`   | `"1"`                                |
| Attribute `mcp.method.name`      | `"initialize"`                       |
| Attribute `mcp.session.id`       | `"8267461134f24305af708e66b8eda71a"` |
| Attribute `mcp.protocol.version` | `"2025-06-18"`                       |
| Attribute `network.transport`    | `"pipe"`                             |

MCP server span (`s2`):

| Property                         | Value                                |
| :------------------------------- | :----------------------------------- |
| Span name                        | `"initialize"`                       |
| Span kind                        | `SERVER`                             |
| Span parent                      | `s1` (MCP client span)               |
| Span status                      | `UNSET`                              |
| Attribute `jsonrpc.request.id`   | `"1"`                                |
| Attribute `mcp.method.name`      | `"initialize"`                       |
| Attribute `mcp.session.id`       | `"8267461134f24305af708e66b8eda71a"` |
| Attribute `mcp.protocol.version` | `"2025-06-18"`                       |
| Attribute `network.transport`    | `"pipe"`                             |

#### Tool call

```
invoke_agent weather-forecast-agent (INTERNAL, trace=t1, span=s1)       # GenAI agent
  |
  -- chat {model} - (CLIENT, trace=t1, span=s2, parent=s1)              # GenAI model client
  |
  -- tools/call get-weather - (CLIENT, trace=t1, span=s3, parent=s1)    # MCP client
  |   |
  |   --- tools/call get-weather (SERVER, trace=t1, span=s4, parent=s3) # MCP server
  |
  -- chat {model} - (CLIENT, trace=t1, span=s5, parent=s1)              # GenAI model client
```

MCP client span (`s3`):

| Property                               | Value                                                                                                                                                     |
| :------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Span name                              | `"tools/call get-weather"`                                                                                                                                |
| Span kind                              | `CLIENT`                                                                                                                                                  |
| Span status                            | `UNSET`                                                                                                                                                   |
| Attribute `gen_ai.operation.name`      | `"execute_tool"`                                                                                                                                          |
| Attribute `gen_ai.tool.call.arguments` | (if enabled)<br>{<br>&nbsp;&nbsp;&nbsp;&nbsp;"location": "San Francisco?",<br>&nbsp;&nbsp;&nbsp;&nbsp;"date": "2025-10-01"<br>}                           |
| Attribute `gen_ai.tool.call.result`    | (if enabled)<br>{<br>&nbsp;&nbsp;"temperature_range": {<br>&nbsp;&nbsp;&nbsp;&nbsp;"high": 75,<br>&nbsp;&nbsp;&nbsp;&nbsp;"low": 60<br>&nbsp;&nbsp;}<br>} |
| Attribute `gen_ai.tool.name`           | `"get-weather"`                                                                                                                                           |
| Attribute `jsonrpc.request.id`         | `"3"`                                                                                                                                                     |
| Attribute `mcp.method.name`            | `"tools/call"`                                                                                                                                            |
| Attribute `mcp.session.id`             | `"8267461134f24305af708e66b8eda71a"`                                                                                                                      |
| Attribute `mcp.protocol.version`       | `"2025-06-18"`                                                                                                                                            |
| Attribute `network.transport`          | `"pipe"`                                                                                                                                                  |

MCP server span (`s4`):

| Property                               | Value                                                                                                                                                     |
| :------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Span name                              | `"tools/call get-weather"`                                                                                                                                |
| Span kind                              | `SERVER`                                                                                                                                                  |
| Span parent                            | `s3` (MCP client span)                                                                                                                                    |
| Span status                            | `UNSET`                                                                                                                                                   |
| Attribute `gen_ai.operation.name`      | `"execute_tool"`                                                                                                                                          |
| Attribute `gen_ai.tool.call.arguments` | (if enabled)<br>{<br>&nbsp;&nbsp;&nbsp;&nbsp;"location": "San Francisco?",<br>&nbsp;&nbsp;&nbsp;&nbsp;"date": "2025-10-01"<br>}                           |
| Attribute `gen_ai.tool.call.result`    | (if enabled)<br>{<br>&nbsp;&nbsp;"temperature_range": {<br>&nbsp;&nbsp;&nbsp;&nbsp;"high": 75,<br>&nbsp;&nbsp;&nbsp;&nbsp;"low": 60<br>&nbsp;&nbsp;}<br>} |
| Attribute `gen_ai.tool.name`           | `"get-weather"`                                                                                                                                           |
| Attribute `jsonrpc.request.id`         | `"3"`                                                                                                                                                     |
| Attribute `mcp.method.name`            | `"tools/call"`                                                                                                                                            |
| Attribute `mcp.session.id`             | `"8267461134f24305af708e66b8eda71a"`                                                                                                                      |
| Attribute `mcp.protocol.version`       | `"2025-06-18"`                                                                                                                                            |
| Attribute `network.transport`          | `"pipe"`                                                                                                                                                  |

### Streamable HTTP

In the HTTP examples, we assume that HTTP instrumentation is enabled on both client
and server side along with the MCP instrumentation.

#### Initialize

```
initialize (CLIENT, trace=t1, span=s1)                  # MCP client
 |
 -- POST - (CLIENT, trace=t1, span=s2, parent=s1)       # HTTP client
 |   |
 |   --- POST - (SERVER, trace=t1, span=s3, parent=s2)  # HTTP server
 |
 -- initialize - (SERVER, trace=t1, span=s4, parent=s1) # MCP server
 |
 -- HTTP - (CLIENT, trace=t1, span=s5, parent=s1)       # HTTP client - notifications channel
```

Here, in addition to MCP client and server spans, we see HTTP client (`s3`)
and server (`s4`) spans. MCP server span remains a child of the MCP client span
(`s1`) and has a link to HTTP server span (`s3`) that was current when MCP server
span started.

MCP client span (`s1`):

| Property                             | Value                                |
| :----------------------------------- | :----------------------------------- |
| Span name                            | `"initialize"`                       |
| Span kind                            | `CLIENT`                             |
| Span status                          | `UNSET`                              |
| Attribute `jsonrpc.request.id`       | `"1"`                                |
| Attribute `mcp.method.name`          | `"initialize"`                       |
| Attribute `mcp.request.id`           | `"1"`                                |
| Attribute `mcp.session.id`           | `"8267461134f24305af708e66b8eda71a"` |
| Attribute `mcp.protocol.version`     | `"2025-06-18"`                       |
| Attribute `network.protocol.name   ` | `"http"`                             |
| Attribute `network.protocol.version` |`"2"`                                 |
| Attribute `network.transport`        | `"tcp"`                              |

MCP server span (`s4`):

| Property                             | Value                                |
| :----------------------------------- | :----------------------------------- |
| Span name                            | `"initialize"`                       |
| Span kind                            | `SERVER`                             |
| Span parent                          | `s1` (MCP client span)               |
| Span links                           | [`s3`] (HTTP server span)            |
| Span status                          | `UNSET`                              |
| Attribute `jsonrpc.request.id`       | `"1"`                                |
| Attribute `mcp.method.name`          | `"initialize"`                       |
| Attribute `mcp.session.id`           | `"8267461134f24305af708e66b8eda71a"` |
| Attribute `mcp.protocol.version`     | `"2025-06-18"`                       |
| Attribute `network.protocol.name   ` | `"http"`                             |
| Attribute `network.protocol.version` | `"2"`                                |
| Attribute `network.transport`        | `"tcp"`                              |

#### Tool call

```
invoke_agent weather-forecast-agent (INTERNAL, trace=t1, span=s1)       # GenAI agent
  |
  -- chat {model} - (CLIENT, trace=t1, span=s2, parent=s1)              # GenAI model
  |   |
  |   --- POST (CLIENT, trace=t1, span=s3, parent=s2)                   # HTTP client
  |
  -- tools/call get-weather - (CLIENT, trace=t1, span=s4, parent=s1)    # MCP client
  |   |
  |   --- POST - (CLIENT, trace=t1, span=s5, parent=s4)                 # HTTP client
  |   |   |
  |   |   ---- POST - (SERVER, trace=t1, span=s6, parent=s5)            # HTTP server
  |   |
  |   --- tools/call get-weather (SERVER, trace=t1, span=s7, parent=s4) # MCP server
  |
  -- chat {model} - (CLIENT, trace=t1, span=s8, parent=s1)              # GenAI model
  |   |
  |   --- POST (CLIENT, trace=t1, span=s9, parent=s8)                   # HTTP server
```

Similarly to HTTP `initialize` example, MCP server (`s7`) span becomes a child of
MCP client span (`s4`).

MCP client span (`s4`):

| Property                               | Value                                                                                                                                                     |
| :------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Span name                              | `"tools/call get-weather"`                                                                                                                                |
| Span kind                              | `CLIENT`                                                                                                                                                  |
| Span status                            | `UNSET`                                                                                                                                                   |
| Attribute `gen_ai.operation.name`      | `"execute_tool"`                                                                                                                                          |
| Attribute `gen_ai.tool.call.arguments` | (if enabled)<br>{<br>&nbsp;&nbsp;&nbsp;&nbsp;"location": "San Francisco?",<br>&nbsp;&nbsp;&nbsp;&nbsp;"date": "2025-10-01"<br>}                           |
| Attribute `gen_ai.tool.call.result`    | (if enabled)<br>{<br>&nbsp;&nbsp;"temperature_range": {<br>&nbsp;&nbsp;&nbsp;&nbsp;"high": 75,<br>&nbsp;&nbsp;&nbsp;&nbsp;"low": 60<br>&nbsp;&nbsp;}<br>} |
| Attribute `gen_ai.tool.name`           | `"get-weather"`                                                                                                                                           |
| Attribute `jsonrpc.request.id`         | `"3"`                                                                                                                                                     |
| Attribute `mcp.method.name`            | `"tools/call"`                                                                                                                                            |
| Attribute `mcp.session.id`             | `"8267461134f24305af708e66b8eda71a"`                                                                                                                      |
| Attribute `mcp.protocol.version`       | `"2025-06-18"`                                                                                                                                            |
| Attribute `network.protocol.name   `   | `"http"`                                                                                                                                                  |
| Attribute `network.protocol.version`   | `"2"`                                                                                                                                                     |
| Attribute `network.transport`          | `"tcp"`                                                                                                                                                   |

MCP server span (`s7`):

| Property                               | Value                                                                                                                                                     |
| :------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Span name                              | `"tools/call get-weather"`                                                                                                                                |
| Span kind                              | `SERVER`                                                                                                                                                  |
| Span parent                            | `s4` (MCP client span)                                                                                                                                    |
| Span links                             | [`s6`] (HTTP server span)                                                                                                                                 |
| Span status                            | `UNSET`                                                                                                                                                   |
| Attribute `gen_ai.operation.name`      | `"execute_tool"`                                                                                                                                          |
| Attribute `gen_ai.tool.call.arguments` | (if enabled)<br>{<br>&nbsp;&nbsp;&nbsp;&nbsp;"location": "San Francisco?",<br>&nbsp;&nbsp;&nbsp;&nbsp;"date": "2025-10-01"<br>}                           |
| Attribute `gen_ai.tool.call.result`    | (if enabled)<br>{<br>&nbsp;&nbsp;"temperature_range": {<br>&nbsp;&nbsp;&nbsp;&nbsp;"high": 75,<br>&nbsp;&nbsp;&nbsp;&nbsp;"low": 60<br>&nbsp;&nbsp;}<br>} |
| Attribute `gen_ai.tool.name`           | `"get-weather"`                                                                                                                                           |
| Attribute `jsonrpc.request.id`         | `"3"`                                                                                                                                                     |
| Attribute `mcp.method.name`            | `"tools/call"`                                                                                                                                            |
| Attribute `mcp.session.id`             | `"8267461134f24305af708e66b8eda71a"`                                                                                                                      |
| Attribute `mcp.protocol.version`       | `"2025-06-18"`                                                                                                                                            |
| Attribute `network.protocol.name   `   | `"http"`                                                                                                                                                  |
| Attribute `network.protocol.version`   | `"2"`                                                                                                                                                     |
| Attribute `network.transport`          | `"tcp"`                                                                                                                                                   |
