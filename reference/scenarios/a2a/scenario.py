"""Reference implementation showcase for an A2A (Agent-to-Agent) client and server.

Demonstrates setting `gen_ai.main_agent` entity resource attributes on the
OpenTelemetry Resource for the logical top-level agent process, while an A2A
AgentExecutor processes tasks over an ASGI transport and emits server-side spans.
A separate client tracer demonstrates client-side telemetry (`invoke_agent_client`).
"""

import asyncio
import json

import httpx
from a2a.client import ClientConfig, create_client
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_rest_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentInterface, Message, Part, Role, SendMessageRequest
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from reference_shared import flush_and_shutdown, setup_otel
from starlette.applications import Starlette

_server_tracer = trace.get_tracer("gen_ai.reference.server")
_client_tracer = trace.get_tracer("gen_ai.reference.client")


class ShowcaseExecutor(AgentExecutor):
    """An A2A AgentExecutor implementation showcasing server-side OTel telemetry."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        print("  [a2a_showcase] ShowcaseExecutor.execute running on A2A server")

        invoke_agent_attrs = {
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": "Travel Assistant",
            "gen_ai.conversation.id": "a2a-session-42",
            "gen_ai.input.messages": json.dumps(
                [{"role": "user", "parts": [{"type": "text", "content": "Find me a flight to Seattle."}]}]
            ),
        }

        with _server_tracer.start_as_current_span(
            "invoke_agent Travel Assistant", attributes=invoke_agent_attrs
        ) as invoke_span:
            tool_attrs = {
                "gen_ai.operation.name": "execute_tool",
                "gen_ai.tool.name": "search_flights",
                "gen_ai.tool.type": "function",
                "gen_ai.tool.call.id": "call_flight_123",
                "gen_ai.tool.call.arguments": json.dumps({"destination": "Seattle"}),
                "gen_ai.tool.call.result": json.dumps({"status": "found", "flight": "FL-101"}),
            }
            with _server_tracer.start_as_current_span("execute_tool search_flights", attributes=tool_attrs):
                pass

            invoke_span.set_attribute(
                "gen_ai.output.messages",
                json.dumps(
                    [{"role": "assistant", "parts": [{"type": "text", "content": "I found flight FL-101 to Seattle."}]}]
                ),
            )

        msg = Message(
            role=Role.ROLE_AGENT,
            message_id="msg-res-1",
            parts=[Part(text="I found flight FL-101 to Seattle.")],
        )
        await event_queue.enqueue_event(msg)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass


async def run_a2a_showcase():
    """Run an A2A client app invoking the A2A server over an in-memory ASGI transport."""
    card = AgentCard(
        name="Travel Assistant",
        description="Top-level travel planning A2A agent service.",
        supported_interfaces=[
            AgentInterface(
                url="http://a2a-server",
                protocol_binding="HTTP+JSON",
                protocol_version="1.0",
            )
        ],
    )
    handler = DefaultRequestHandler(
        agent_executor=ShowcaseExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    app = Starlette(routes=create_rest_routes(handler))

    client = await create_client(
        agent=card,
        client_config=ClientConfig(
            supported_protocol_bindings=["HTTP+JSON"],
            httpx_client=httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://a2a-server",
            ),
        ),
    )

    print("  [a2a_showcase] Client app calling A2A server over ASGI transport")
    client_attrs = {
        "gen_ai.operation.name": "invoke_agent",
        "gen_ai.agent.id": "urn:agent:travel-assistant:v1",
        "gen_ai.agent.name": "Travel Assistant",
        "gen_ai.conversation.id": "a2a-session-42",
        "gen_ai.input.messages": json.dumps(
            [{"role": "user", "parts": [{"type": "text", "content": "Find me a flight to Seattle."}]}]
        ),
    }
    with _client_tracer.start_as_current_span("invoke_agent Travel Assistant (client)", attributes=client_attrs):
        req = SendMessageRequest(
            message=Message(
                role=Role.ROLE_USER,
                message_id="msg-req-1",
                parts=[Part(text="Find me a flight to Seattle.")],
            )
        )
        async for _ in client.send_message(req):
            pass


def main():
    print("=== A2A Agent Showcase (`gen_ai.main_agent` entity + ASGI transport) ===")

    resource = Resource.create(
        {
            "gen_ai.main_agent.id": "urn:agent:travel-assistant:v1",
            "gen_ai.main_agent.name": "Travel Assistant",
            "gen_ai.main_agent.description": "Top-level travel planning A2A agent service.",
        }
    )

    tp, lp, mp = setup_otel(resource=resource)
    asyncio.run(run_a2a_showcase())
    flush_and_shutdown(tp, lp, mp)


if __name__ == "__main__":
    main()
