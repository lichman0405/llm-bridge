# app/api/v1/endpoints/anthropic_proxy.py
# This module defines the proxy endpoint for handling requests to the Anthropic API.
# It transforms incoming requests to the standardized format and manages streaming responses.
# Author: Shibo Li
# Date: 2025-07-14
# Version: 0.1.0

import json
import os
import uuid
from fastapi import APIRouter, Request as FastAPIRequest
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
    """Transforms a complex Anthropic request, applying the default model override if set."""
    
    # 读取环境变量以实现强制覆盖
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
        model=final_model_name, # 使用最终确定的模型名称
        messages=standard_messages,
        stream=anthropic_request.stream,
        temperature=anthropic_request.temperature,
        top_p=anthropic_request.top_p,
        max_tokens=anthropic_request.max_tokens,
    )


async def _full_response_translator(
    standard_request: StandardizedChatRequest,
    adapter_response: Union[Dict[str, Any], AsyncGenerator[bytes, None]],
) -> AsyncGenerator[str, None]:
    # This function remains the same.
    start_event_data = {
        "type": "message_start",
        "message": {
            "id": f"msg-proxy-{uuid.uuid4()}",
            "type": "message",
            "role": "assistant",
            "content": [],
            "model": standard_request.model,
            "stop_reason": None,
            "usage": {"input_tokens": 0, "output_tokens": 0},
        },
    }
    yield f'event: message_start\ndata: {json.dumps(start_event_data)}\n\n'

    if isinstance(adapter_response, AsyncGenerator):
        async for chunk in adapter_response:
            chunk_str = chunk.decode("utf-8").strip()
            if not chunk_str or chunk_str == "data: [DONE]":
                continue
            try:
                data = json.loads(chunk_str[6:])
                delta = data.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content")
                if content:
                    delta_event_data = {
                        "type": "content_block_delta",
                        "index": 0,
                        "delta": {"type": "text_delta", "text": content},
                    }
                    yield f'event: content_block_delta\ndata: {json.dumps(delta_event_data)}\n\n'
            except json.JSONDecodeError:
                console.warning(f"Could not decode stream chunk: {chunk_str}")
                continue
    
    stop_event_data = {"type": "message_stop"}
    yield f'event: message_stop\ndata: {json.dumps(stop_event_data)}\n\n'


@router.post("/v1/messages", response_model=None)
async def anthropic_proxy(request: AnthropicChatRequest) -> Union[StreamingResponse, JSONResponse]:
    # This function also remains the same.
    try:
        console.info(f"Anthropic proxy received request for original model: {request.model}")
        standard_request = _transform_anthropic_to_standard(request)
        
        adapter = get_adapter(model_name=standard_request.model)
        adapter_response = await adapter.chat_completions(standard_request)
        
        if standard_request.stream:
            final_stream = _full_response_translator(standard_request, adapter_response)
            return StreamingResponse(final_stream, media_type="text/event-stream")
        else:
            # Ensure adapter_response is a dict for non-streaming responses
            if isinstance(adapter_response, dict):
                translated_response = {
                    "id": f"msg-proxy-{uuid.uuid4()}",
                    "type": "message",
                    "role": "assistant",
                    "model": adapter_response.get("model", standard_request.model),
                    "content": [{"type": "text","text": adapter_response.get("choices", [{}])[0].get("message", {}).get("content", "")}],
                    "stop_reason": "end_turn",
                    "usage": adapter_response.get("usage", {"prompt_tokens": 0, "completion_tokens": 0}),
                }
                return JSONResponse(content=translated_response)
            else:
                raise ValueError("Expected dict response for non-streaming request")

    except Exception as e:
        console.exception(f"FATAL: An unhandled error occurred in anthropic_proxy: {e}")
        error_content = {"type": "error", "error": {"type": "internal_server_error", "message": str(e)}}
        return JSONResponse(status_code=500, content=error_content)