"""Reference implementation for Vertex AI.

Exercises: chat, chat_streaming
against a mock Vertex AI server, with manual OTel spans.
"""

import json
import os
import warnings

from reference_shared import flush_and_shutdown, reference_event_logger, reference_tracer, setup_otel

MOCK_BASE_URL = os.environ["MOCK_LLM_URL"]

# The Vertex AI gapic REST transport defaults to HTTPS. Monkey-patch the
# transport to use plain HTTP so we can talk to the local mock server.
from google.cloud.aiplatform_v1.services.prediction_service.transports.rest import (  # noqa: E402
    PredictionServiceRestTransport,
)

_original_rest_init = PredictionServiceRestTransport.__init__


def _patched_rest_init(self, **kwargs):
    kwargs.setdefault("url_scheme", "http")
    return _original_rest_init(self, **kwargs)


PredictionServiceRestTransport.__init__ = _patched_rest_init

_reference_tracer = reference_tracer()

# Maps Vertex `Modality` values to the `gen_ai.usage.<modality>.*` suffix.
_MODALITY_MAP = {
    "TEXT": "text",
    "IMAGE": "image",
    "AUDIO": "audio",
    "VIDEO": "video",
    "DOCUMENT": "document",
}


def _modality_usage_attributes(usage_metadata):
    """Map Vertex per-modality token details to `gen_ai.usage.<modality>.*` attributes."""
    attrs = {}
    for details, suffix in (
        (getattr(usage_metadata, "prompt_tokens_details", None), "input_tokens"),
        (getattr(usage_metadata, "candidates_tokens_details", None), "output_tokens"),
        (getattr(usage_metadata, "cache_tokens_details", None), "cache_read.input_tokens"),
    ):
        for entry in details or []:
            raw = getattr(entry, "modality", None)
            name = getattr(raw, "name", str(raw)).split(".")[-1].upper()
            modality = _MODALITY_MAP.get(name)
            count = getattr(entry, "token_count", None)
            if modality and count:
                attrs[f"gen_ai.usage.{modality}.{suffix}"] = count
    return attrs


def _usage_attributes(um):
    """All `gen_ai.usage.*` attributes derivable from Vertex usage metadata.

    Returned as a dict so the exact same attributes can be set on both the span
    and the inference-details event.
    """
    attrs = {}
    reasoning_tokens = getattr(um, "thoughts_token_count", None) or 0
    cache_read_tokens = getattr(um, "cached_content_token_count", None) or 0
    tool_use_tokens = getattr(um, "tool_use_prompt_token_count", None) or 0
    if um.prompt_token_count:
        attrs["gen_ai.usage.input_tokens"] = um.prompt_token_count + tool_use_tokens
    output_tokens = (um.candidates_token_count or 0) + reasoning_tokens
    if output_tokens:
        attrs["gen_ai.usage.output_tokens"] = output_tokens
    if cache_read_tokens:
        attrs["gen_ai.usage.cache_read.input_tokens"] = cache_read_tokens
    if tool_use_tokens:
        attrs["gen_ai.usage.tool.input_tokens"] = tool_use_tokens
    if reasoning_tokens:
        attrs["gen_ai.usage.reasoning.output_tokens"] = reasoning_tokens
    attrs.update(_modality_usage_attributes(um))
    return attrs


def _emit_inference_event(request_model, input_messages, output_messages, response_model, finish_reason, usage):
    """Emit an inference-details event carrying the same usage attributes as the span."""
    event_attrs = {
        "gen_ai.operation.name": "chat",
        "gen_ai.request.model": request_model,
        "gen_ai.input.messages": json.dumps(input_messages),
        "gen_ai.output.messages": json.dumps(output_messages),
    }
    if response_model:
        event_attrs["gen_ai.response.model"] = response_model
    if finish_reason:
        event_attrs["gen_ai.response.finish_reasons"] = [finish_reason]
    event_attrs.update(usage)
    reference_event_logger().emit(
        event_name="gen_ai.client.inference.operation.details",
        body="Inference operation details",
        attributes=event_attrs,
    )


def _mock_host():
    """Return host:port from MOCK_BASE_URL (strip scheme)."""
    return MOCK_BASE_URL.replace("http://", "").replace("https://", "")


def _init_vertexai():
    """Initialize Vertex AI SDK pointing at the mock server."""
    import vertexai
    from google.auth.credentials import AnonymousCredentials

    vertexai.init(
        project="test-project",
        location="us-central1",
        credentials=AnonymousCredentials(),
        api_endpoint=_mock_host(),
        api_transport="rest",
    )


def run_chat():
    """Scenario: basic chat completion with reference implementation."""
    from vertexai.generative_models import GenerativeModel

    print("  [chat] basic chat completion via Vertex AI (reference implementation)")
    request_model = "gemini-2.0-flash"
    span_attributes = {
        "gen_ai.operation.name": "chat",
        "gen_ai.provider.name": "gcp.vertex_ai",
        "gen_ai.request.model": request_model,
    }
    with _reference_tracer.start_as_current_span("chat gemini-2.0-flash", attributes=span_attributes) as span:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            warnings.simplefilter("ignore", UserWarning)
            model = GenerativeModel(request_model)
            prompt_text = "Say hello."
            response = model.generate_content(prompt_text)
        response_model = response.to_dict().get("modelVersion")
        if response_model:
            span.set_attribute("gen_ai.response.model", response_model)
        finish_reason = (
            str(response.candidates[0].finish_reason.name)
            if response.candidates and response.candidates[0].finish_reason
            else None
        )
        if finish_reason:
            span.set_attribute("gen_ai.response.finish_reasons", [finish_reason])
        usage = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = _usage_attributes(response.usage_metadata)
            for attr, value in usage.items():
                span.set_attribute(attr, value)

        input_messages = [{"role": "user", "parts": [{"type": "text", "content": prompt_text}]}]
        output_messages = [
            {
                "role": "assistant",
                "parts": [{"type": "text", "content": response.text}],
                "finish_reason": finish_reason,
            }
        ]
        _emit_inference_event(request_model, input_messages, output_messages, response_model, finish_reason, usage)

        print(f"    -> {response.text[:60]}")


def run_chat_tool_call():
    """Scenario: chat with tool calling with reference implementation."""
    from vertexai.generative_models import FunctionDeclaration, GenerativeModel, Tool

    print("  [chat_tool_call] chat with tool calling via Vertex AI (reference implementation)")
    request_model = "gemini-2.0-flash"
    get_weather_func = FunctionDeclaration(
        name="get_weather",
        description="Get the current weather",
        parameters={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
            },
            "required": ["location"],
        },
    )
    tool = Tool(function_declarations=[get_weather_func])
    span_attributes_2 = {
        "gen_ai.operation.name": "chat",
        "gen_ai.provider.name": "gcp.vertex_ai",
        "gen_ai.request.model": request_model,
    }
    with _reference_tracer.start_as_current_span("chat gemini-2.0-flash", attributes=span_attributes_2) as span:
        span.set_attribute(
            "gen_ai.tool.definitions",
            json.dumps(
                [
                    {
                        "function_declarations": [
                            {
                                "name": "get_weather",
                                "description": "Get the current weather",
                                "parameters": {
                                    "type": "object",
                                    "properties": {"location": {"type": "string", "description": "City name"}},
                                    "required": ["location"],
                                },
                            }
                        ]
                    }
                ]
            ),
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            warnings.simplefilter("ignore", UserWarning)
            model = GenerativeModel(request_model)
            response = model.generate_content(
                "What's the weather in Seattle?",
                tools=[tool],
            )
        response_model = response.to_dict().get("modelVersion")
        if response_model:
            span.set_attribute("gen_ai.response.model", response_model)
        if response.candidates and response.candidates[0].finish_reason:
            span.set_attribute("gen_ai.response.finish_reasons", [str(response.candidates[0].finish_reason.name)])
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            if response.usage_metadata.prompt_token_count:
                span.set_attribute("gen_ai.usage.input_tokens", response.usage_metadata.prompt_token_count)
            if response.usage_metadata.candidates_token_count:
                span.set_attribute("gen_ai.usage.output_tokens", response.usage_metadata.candidates_token_count)
        part = response.candidates[0].content.parts[0]
        if hasattr(part, "function_call") and part.function_call and part.function_call.name:
            print(f"    -> tool_call: {part.function_call.name}")
        else:
            print(f"    -> {response.text[:60]}")


def run_chat_streaming():
    """Scenario: streaming chat completion with reference implementation."""
    from vertexai.generative_models import GenerativeModel

    print("  [chat_streaming] streaming chat completion via Vertex AI (reference implementation)")
    request_model = "gemini-2.0-flash"
    span_attributes_3 = {
        "gen_ai.operation.name": "chat",
        "gen_ai.provider.name": "gcp.vertex_ai",
        "gen_ai.request.model": request_model,
    }
    with _reference_tracer.start_as_current_span("chat gemini-2.0-flash", attributes=span_attributes_3) as span:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            warnings.simplefilter("ignore", UserWarning)
            model = GenerativeModel(request_model)
            text = ""
            last_chunk = None
            for chunk in model.generate_content("Tell me a joke.", stream=True):
                text += chunk.text
                last_chunk = chunk
        if last_chunk:
            response_model = last_chunk.to_dict().get("modelVersion")
            if response_model:
                span.set_attribute("gen_ai.response.model", response_model)
        if last_chunk and last_chunk.candidates and last_chunk.candidates[0].finish_reason:
            span.set_attribute("gen_ai.response.finish_reasons", [str(last_chunk.candidates[0].finish_reason.name)])
        if last_chunk and hasattr(last_chunk, "usage_metadata") and last_chunk.usage_metadata:
            if last_chunk.usage_metadata.prompt_token_count:
                span.set_attribute("gen_ai.usage.input_tokens", last_chunk.usage_metadata.prompt_token_count)
            if last_chunk.usage_metadata.candidates_token_count:
                span.set_attribute("gen_ai.usage.output_tokens", last_chunk.usage_metadata.candidates_token_count)
        print(f"    -> {text[:60]}")


def run_chat_multimodal():
    """Scenario: multimodal (text + image + audio + video + document) input, per-modality usage."""
    from vertexai.generative_models import GenerativeModel, Part

    print("  [chat_multimodal] multimodal input chat via Vertex AI (reference implementation)")
    request_model = "gemini-2.0-flash"
    # Payload bytes are ignored by the mock, which only inspects the MIME type.
    blob = b"\x00" * 16
    span_attributes = {
        "gen_ai.operation.name": "chat",
        "gen_ai.provider.name": "gcp.vertex_ai",
        "gen_ai.request.model": request_model,
    }
    with _reference_tracer.start_as_current_span("chat gemini-2.0-flash", attributes=span_attributes) as span:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            warnings.simplefilter("ignore", UserWarning)
            model = GenerativeModel(request_model)
            response = model.generate_content(
                [
                    "Summarize the attached media.",
                    Part.from_data(data=blob, mime_type="image/png"),
                    Part.from_data(data=blob, mime_type="audio/wav"),
                    Part.from_data(data=blob, mime_type="video/mp4"),
                    Part.from_data(data=blob, mime_type="application/pdf"),
                ]
            )
        response_model = response.to_dict().get("modelVersion")
        if response_model:
            span.set_attribute("gen_ai.response.model", response_model)
        finish_reason = (
            str(response.candidates[0].finish_reason.name)
            if response.candidates and response.candidates[0].finish_reason
            else None
        )
        if finish_reason:
            span.set_attribute("gen_ai.response.finish_reasons", [finish_reason])
        usage = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = _usage_attributes(response.usage_metadata)
            for attr, value in usage.items():
                span.set_attribute(attr, value)

        input_messages = [
            {
                "role": "user",
                "parts": [
                    {"type": "text", "content": "Summarize the attached media."},
                    {"type": "blob", "mime_type": "image/png"},
                    {"type": "blob", "mime_type": "audio/wav"},
                    {"type": "blob", "mime_type": "video/mp4"},
                    {"type": "blob", "mime_type": "application/pdf"},
                ],
            }
        ]
        output_messages = [
            {"role": "assistant", "parts": [{"type": "text", "content": response.text}], "finish_reason": finish_reason}
        ]
        _emit_inference_event(request_model, input_messages, output_messages, response_model, finish_reason, usage)
        print("    -> multimodal usage captured")


def main():
    print("=== Reference Implementation: Vertex AI ===")

    tp, lp, mp = setup_otel()
    # NO instrument() call - reference implementation only
    _init_vertexai()

    run_chat()
    run_chat_tool_call()
    run_chat_multimodal()
    run_chat_streaming()

    flush_and_shutdown(tp, lp, mp)


if __name__ == "__main__":
    main()
