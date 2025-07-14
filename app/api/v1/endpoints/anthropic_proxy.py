# app/api/v1/endpoints/anthropic_proxy.py
# This module defines the proxy endpoint for handling requests to the Anthropic API.
# It transforms incoming requests to the standardized format and manages streaming responses.
# Author: Shibo Li
# Date: 2025-07-14
# Version: 0.1.0

import json
import os
import uuid
from fastapi import APIRouter, HTTPException, Request as FastAPIRequest
from fastapi.responses import StreamingResponse, JSONResponse
from typing import AsyncGenerator, Union, List, Dict, Any

from app.core.schemas import (
    StandardizedChatRequest,
    ChatMessage,
    AnthropicChatRequest,
    AnthropicContentBlock,
)
from app.services.model_manager import get_adapter
from app.core.logger import console

router = APIRouter()


def _extract_text_from_anthropic_content(
    content: Union[str, List[AnthropicContentBlock]],
) -> str:
    """Extracts and concatenates text from Anthropic's rich content format."""
    if isinstance(content, str):
        return content

    full_text = []
    if content:
        for block in content:
            if block.type == "text" and block.text:
                full_text.append(block.text)
    return "".join(full_text)


def _transform_anthropic_to_standard(
    anthropic_request: AnthropicChatRequest,
) -> StandardizedChatRequest:
    """Transforms a complex Anthropic request to our internal standard format."""
    default_model_override = os.getenv("DEFAULT_MODEL_OVERRIDE")
    final_model_name = (
        default_model_override
        if default_model_override
        else anthropic_request.model
    )

    if default_model_override:
        console.info(
            f"Model override active: '{anthropic_request.model}' -> '{final_model_name}'"
        )

    standard_messages = []
    if anthropic_request.system:
        system_text = _extract_text_from_anthropic_content(anthropic_request.system)
        if system_text:
            standard_messages.append(ChatMessage(role="system", content=system_text))

    for msg in anthropic_request.messages:
        content_text = _extract_text_from_anthropic_content(msg.content)
        if content_text:
            standard_messages.append(ChatMessage(role=msg.role, content=content_text))

    return StandardizedChatRequest(
        model=final_model_name,
        messages=standard_messages,
        stream=anthropic_request.stream,
        temperature=anthropic_request.temperature,
        top_p=anthropic_request.top_p,
        max_tokens=anthropic_request.max_tokens,
    )


async def _openai_to_anthropic_stream_translator(
    openai_stream: AsyncGenerator[bytes, None],
) -> AsyncGenerator[str, None]:
    """Translates an OpenAI SSE stream to an Anthropic SSE stream."""
    async for chunk in openai_stream:
        chunk_str = chunk.decode("utf-8").strip()
        if not chunk_str:
            continue

        if chunk_str == "data: [DONE]":
            yield 'event: message_stop\ndata: {"type": "message_stop"}\n\n'
            break

        try:
            data = json.loads(chunk_str[6:])
            delta = data.get("choices", [{}])[0].get("delta", {})
            content = delta.get("content")

            if content:
                response_data = {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {"type": "text_delta", "text": content},
                }
                yield f'event: content_block_delta\ndata: {json.dumps(response_data)}\n\n'

        except json.JSONDecodeError:
            console.warning(f"Could not decode stream chunk: {chunk_str}")
            continue

def _openai_to_anthropic_response_translator(
    openai_response: Dict[str, Any]
) -> Dict[str, Any]:
    """(New) Translates a single OpenAI JSON response to Anthropic's format."""
    final_content = openai_response.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    return {
        "id": f"msg-proxy-{uuid.uuid4()}",
        "type": "message",
        "role": "assistant",
        "model": openai_response.get("model", "proxied-model"),
        "content": [{"type": "text", "text": final_content}],
        "stop_reason": "end_turn",
        "usage": openai_response.get("usage", {"prompt_tokens": 0, "completion_tokens": 0}),
    }


@router.post("/v1/messages", response_model=None)
async def anthropic_proxy(request: AnthropicChatRequest) -> Union[StreamingResponse, JSONResponse]:
    try:
        console.info(f"Anthropic proxy received request for original model: {request.model}")

        standard_request = _transform_anthropic_to_standard(request)
        adapter = get_adapter(model_name=standard_request.model)

        # This call now correctly returns either a stream or a dict
        response_data = await adapter.chat_completions(standard_request)

        # Handle both streaming and non-streaming cases
        if standard_request.stream:
            anthropic_stream = _openai_to_anthropic_stream_translator(response_data)
            return StreamingResponse(anthropic_stream, media_type="text/event-stream")
        else:
            # New logic to handle the non-streaming case
            translated_response = _openai_to_anthropic_response_translator(response_data)
            return JSONResponse(content=translated_response)

    except ValueError as e:
        console.error(f"Anthropic proxy validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        console.exception(f"Unexpected Anthropic proxy error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")