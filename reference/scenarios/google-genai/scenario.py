"""Reference implementation for Google GenAI.

Exercises: chat, chat_streaming, embeddings
against a mock Google GenAI server, with manual OTel spans.
"""

import json
import os

from reference_shared import flush_and_shutdown, reference_event_logger, reference_tracer, setup_otel

MOCK_BASE_URL = os.environ["MOCK_LLM_URL"]

_reference_tracer = reference_tracer()

# Maps Google `MediaModality` values to the `gen_ai.usage.<modality>.*` suffix.
_MODALITY_MAP = {
    "TEXT": "text",
    "IMAGE": "image",
    "AUDIO": "audio",
    "VIDEO": "video",
    "DOCUMENT": "document",
}


def _entry_modality(entry):
    raw = getattr(entry, "modality", None)
    name = getattr(raw, "name", str(raw)).split(".")[-1].upper()
    return _MODALITY_MAP.get(name)


def _modality_usage_attributes(usage_metadata):
    """Map Google per-modality token details to `gen_ai.usage.<modality>.*` attributes."""
    attrs = {}
    for details, suffix in (
        (getattr(usage_metadata, "prompt_tokens_details", None), "input_tokens"),
        (getattr(usage_metadata, "candidates_tokens_details", None), "output_tokens"),
        (getattr(usage_metadata, "cache_tokens_details", None), "cache_read.input_tokens"),
    ):
        for entry in details or []:
            modality = _entry_modality(entry)
            count = getattr(entry, "token_count", None)
            if modality and count:
                attrs[f"gen_ai.usage.{modality}.{suffix}"] = count
    return attrs


def _usage_attributes(um):
    """All `gen_ai.usage.*` attributes derivable from Google usage metadata.

    Returned as a dict so the exact same attributes can be set on both the span
    and the inference-details event.
    """
    attrs = {}
    reasoning_tokens = getattr(um, "thoughts_token_count", None) or 0
    cache_read_tokens = getattr(um, "cached_content_token_count", None) or 0
    # Tool-use tokens are reported separately from prompt_token_count, so add
    # them to get the total input token count.
    tool_use_tokens = getattr(um, "tool_use_prompt_token_count", None) or 0
    if um.prompt_token_count:
        # prompt_token_count already includes cached content.
        attrs["gen_ai.usage.input_tokens"] = um.prompt_token_count + tool_use_tokens
    # Google reports "thoughts" (reasoning) tokens separately from the visible
    # candidates, so include them in the output token total.
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


def _emit_inference_event(request_model, input_messages, output_messages, response, usage):
    """Emit an inference-details event carrying the same usage attributes as the span."""
    event_attrs = {
        "gen_ai.operation.name": "chat",
        "gen_ai.request.model": request_model,
        "gen_ai.input.messages": json.dumps(input_messages),
        "gen_ai.output.messages": json.dumps(output_messages),
    }
    if response.model_version:
        event_attrs["gen_ai.response.model"] = response.model_version
    if response.candidates and response.candidates[0].finish_reason:
        event_attrs["gen_ai.response.finish_reasons"] = [str(response.candidates[0].finish_reason)]
    event_attrs.update(usage)
    reference_event_logger().emit(
        event_name="gen_ai.client.inference.operation.details",
        body="Inference operation details",
        attributes=event_attrs,
    )


def run_chat():
    """Scenario: basic chat completion with reference implementation."""
    from google import genai
    from google.genai import types

    print("  [chat] basic chat completion via Google GenAI (reference implementation)")
    client = genai.Client(
        api_key="mock-key",
        http_options=types.HttpOptions(
            base_url=MOCK_BASE_URL,
            api_version="v1beta",
        ),
    )
    request_model = "gemini-2.0-flash"
    span_attributes = {
        "gen_ai.operation.name": "chat",
        "gen_ai.provider.name": "gcp.gemini",
        "gen_ai.request.model": request_model,
    }
    with _reference_tracer.start_as_current_span("chat gemini-2.0-flash", attributes=span_attributes) as span:
        prompt_text = "Say hello."
        response = client.models.generate_content(
            model=request_model,
            contents=prompt_text,
        )
        if response.model_version:
            span.set_attribute("gen_ai.response.model", response.model_version)
        if response.candidates and response.candidates[0].finish_reason:
            span.set_attribute("gen_ai.response.finish_reasons", [str(response.candidates[0].finish_reason)])
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
                "finish_reason": str(response.candidates[0].finish_reason) if response.candidates else None,
            }
        ]
        _emit_inference_event(request_model, input_messages, output_messages, response, usage)

        print(f"    -> {response.text[:60]}")


def run_chat_tool_call():
    """Scenario: chat with tool calling with reference implementation."""
    from google import genai
    from google.genai import types

    print("  [chat_tool_call] chat with tool calling via Google GenAI (reference implementation)")
    client = genai.Client(
        api_key="mock-key",
        http_options=types.HttpOptions(
            base_url=MOCK_BASE_URL,
            api_version="v1beta",
        ),
    )
    request_model = "gemini-2.0-flash"
    tool = types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="get_weather",
                description="Get the current weather",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "location": types.Schema(type="STRING", description="City name"),
                    },
                    required=["location"],
                ),
            )
        ]
    )
    tools = [tool]
    span_attributes_2 = {
        "gen_ai.operation.name": "chat",
        "gen_ai.provider.name": "gcp.gemini",
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
        response = client.models.generate_content(
            model=request_model,
            contents="What's the weather in Seattle?",
            config=types.GenerateContentConfig(tools=tools),
        )
        if response.model_version:
            span.set_attribute("gen_ai.response.model", response.model_version)
        if response.candidates and response.candidates[0].finish_reason:
            span.set_attribute("gen_ai.response.finish_reasons", [str(response.candidates[0].finish_reason)])
        usage = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = _usage_attributes(response.usage_metadata)
            for attr, value in usage.items():
                span.set_attribute(attr, value)

        tool_call = None
        if response.candidates and response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            if hasattr(part, "function_call") and part.function_call:
                tool_call = part.function_call
        input_messages = [
            {"role": "user", "parts": [{"type": "text", "content": "What's the weather in Seattle?"}]}
        ]
        output_messages = [
            {
                "role": "assistant",
                "parts": (
                    [{"type": "tool_call", "name": tool_call.name, "arguments": dict(tool_call.args)}]
                    if tool_call
                    else [{"type": "text", "content": response.text}]
                ),
                "finish_reason": str(response.candidates[0].finish_reason) if response.candidates else None,
            }
        ]
        _emit_inference_event(request_model, input_messages, output_messages, response, usage)
        print(f"    -> tool_call: {tool_call.name}" if tool_call else f"    -> {response.text[:60]}")


def _set_usage(span, um):
    """Set aggregate and per-modality usage attributes on the span; return them."""
    usage = _usage_attributes(um)
    for attr, value in usage.items():
        span.set_attribute(attr, value)
    return usage


def run_chat_multimodal():
    """Scenario: multimodal (text + image + audio + video + document) input, per-modality usage."""
    from google import genai
    from google.genai import types

    print("  [chat_multimodal] multimodal input chat via Google GenAI (reference implementation)")
    client = genai.Client(
        api_key="mock-key",
        http_options=types.HttpOptions(base_url=MOCK_BASE_URL, api_version="v1beta"),
    )
    request_model = "gemini-2.0-flash"
    # Payload bytes are ignored by the mock, which only inspects the MIME type.
    blob = b"\x00" * 16
    span_attributes = {
        "gen_ai.operation.name": "chat",
        "gen_ai.provider.name": "gcp.gemini",
        "gen_ai.request.model": request_model,
    }
    with _reference_tracer.start_as_current_span("chat gemini-2.0-flash", attributes=span_attributes) as span:
        response = client.models.generate_content(
            model=request_model,
            contents=[
                "Summarize the attached media.",
                types.Part.from_bytes(data=blob, mime_type="image/png"),
                types.Part.from_bytes(data=blob, mime_type="audio/wav"),
                types.Part.from_bytes(data=blob, mime_type="video/mp4"),
                types.Part.from_bytes(data=blob, mime_type="application/pdf"),
            ],
        )
        if response.model_version:
            span.set_attribute("gen_ai.response.model", response.model_version)
        if response.candidates and response.candidates[0].finish_reason:
            span.set_attribute("gen_ai.response.finish_reasons", [str(response.candidates[0].finish_reason)])
        usage = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = _set_usage(span, response.usage_metadata)

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
            {
                "role": "assistant",
                "parts": [{"type": "text", "content": response.text}],
                "finish_reason": str(response.candidates[0].finish_reason) if response.candidates else None,
            }
        ]
        _emit_inference_event(request_model, input_messages, output_messages, response, usage)
        print("    -> multimodal usage captured")


def run_generate_media():
    """Scenario: image + audio output generation, emitting per-modality output usage."""
    from google import genai
    from google.genai import types

    print("  [generate_media] media generation via Google GenAI (reference implementation)")
    client = genai.Client(
        api_key="mock-key",
        http_options=types.HttpOptions(base_url=MOCK_BASE_URL, api_version="v1beta"),
    )
    request_model = "gemini-2.0-flash"
    # (label, requested output modalities) -> exercises image and audio output token counts.
    for label, modalities in (("image", ["TEXT", "IMAGE"]), ("audio", ["AUDIO"])):
        span_attributes = {
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "gcp.gemini",
            "gen_ai.request.model": request_model,
        }
        with _reference_tracer.start_as_current_span(
            "chat gemini-2.0-flash", attributes=span_attributes
        ) as span:
            response = client.models.generate_content(
                model=request_model,
                contents=f"Generate {label} output.",
                config=types.GenerateContentConfig(response_modalities=modalities),
            )
            if response.model_version:
                span.set_attribute("gen_ai.response.model", response.model_version)
            if response.candidates and response.candidates[0].finish_reason:
                span.set_attribute("gen_ai.response.finish_reasons", [str(response.candidates[0].finish_reason)])
            usage = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = _set_usage(span, response.usage_metadata)

            input_messages = [{"role": "user", "parts": [{"type": "text", "content": f"Generate {label} output."}]}]
            output_parts = []
            for part in (response.candidates[0].content.parts if response.candidates else []) or []:
                if getattr(part, "text", None):
                    output_parts.append({"type": "text", "content": part.text})
                elif getattr(part, "inline_data", None):
                    output_parts.append({"type": "blob", "mime_type": part.inline_data.mime_type})
            output_messages = [
                {
                    "role": "assistant",
                    "parts": output_parts,
                    "finish_reason": str(response.candidates[0].finish_reason) if response.candidates else None,
                }
            ]
            _emit_inference_event(request_model, input_messages, output_messages, response, usage)
            print(f"    -> {label} output usage captured")


def run_chat_streaming():
    """Scenario: streaming chat completion with reference implementation."""
    from google import genai
    from google.genai import types

    print("  [chat_streaming] streaming chat via Google GenAI (reference implementation)")
    client = genai.Client(
        api_key="mock-key",
        http_options=types.HttpOptions(
            base_url=MOCK_BASE_URL,
            api_version="v1beta",
        ),
    )
    request_model = "gemini-2.0-flash"
    span_attributes_3 = {
        "gen_ai.operation.name": "chat",
        "gen_ai.provider.name": "gcp.gemini",
        "gen_ai.request.model": request_model,
    }
    with _reference_tracer.start_as_current_span("chat gemini-2.0-flash", attributes=span_attributes_3) as span:
        text = ""
        last_chunk = None
        for chunk in client.models.generate_content_stream(
            model=request_model,
            contents="Tell me a joke.",
        ):
            if chunk.text:
                text += chunk.text
            last_chunk = chunk
        if last_chunk and last_chunk.model_version:
            span.set_attribute("gen_ai.response.model", last_chunk.model_version)
        if last_chunk and last_chunk.candidates and last_chunk.candidates[0].finish_reason:
            span.set_attribute("gen_ai.response.finish_reasons", [str(last_chunk.candidates[0].finish_reason)])
        if last_chunk and hasattr(last_chunk, "usage_metadata") and last_chunk.usage_metadata:
            if (
                hasattr(last_chunk.usage_metadata, "prompt_token_count")
                and last_chunk.usage_metadata.prompt_token_count
            ):
                span.set_attribute("gen_ai.usage.input_tokens", last_chunk.usage_metadata.prompt_token_count)
            if (
                hasattr(last_chunk.usage_metadata, "candidates_token_count")
                and last_chunk.usage_metadata.candidates_token_count
            ):
                span.set_attribute("gen_ai.usage.output_tokens", last_chunk.usage_metadata.candidates_token_count)
        print(f"    -> {text[:60]}")


def run_embeddings():
    """Scenario: embedding generation with reference implementation."""
    from google import genai
    from google.genai import types

    print("  [embeddings] embedding generation via Google GenAI (reference implementation)")
    client = genai.Client(
        api_key="mock-key",
        http_options=types.HttpOptions(
            base_url=MOCK_BASE_URL,
            api_version="v1beta",
        ),
    )
    request_model = "text-embedding-004"
    span_attributes_4 = {
        "gen_ai.operation.name": "embeddings",
        "gen_ai.provider.name": "gcp.gemini",
        "gen_ai.request.model": request_model,
    }
    with _reference_tracer.start_as_current_span("embeddings text-embedding-004", attributes=span_attributes_4) as span:
        response = client.models.embed_content(
            model=request_model,
            contents="Hello, world!",
        )
        if response.embeddings and response.embeddings[0].values is not None:
            span.set_attribute("gen_ai.embeddings.dimension.count", len(response.embeddings[0].values))
        print(f"    -> embedding dim: {len(response.embeddings[0].values)}")


def main():
    print("=== Reference Implementation: Google GenAI ===")

    tp, lp, mp = setup_otel()
    # NO instrument() call - reference implementation only

    run_chat()
    run_chat_tool_call()
    run_chat_multimodal()
    run_generate_media()
    run_chat_streaming()
    run_embeddings()

    flush_and_shutdown(tp, lp, mp)


if __name__ == "__main__":
    main()
