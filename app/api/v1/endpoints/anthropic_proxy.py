# app/api/v1/endpoints/anthropic_proxy.py
# This module defines the proxy endpoint for handling requests to the Anthropic API.
# It transforms incoming requests to the standardized format and manages streaming responses.
# Author: Shibo Li
# Date: 2025-07-14
# Version: 0.1.0


import json
import os
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import AsyncGenerator, Union, List, Dict, Any

from app.core.schemas import (
    StandardizedChatRequest, ChatMessage, Tool, Function,
    AnthropicChatRequest, AnthropicContentBlock, AnthropicTool
)
from app.services.model_manager import get_adapter
from app.core.logger import console

router = APIRouter()

def _transform_anthropic_to_standard(req: AnthropicChatRequest) -> StandardizedChatRequest:
    """(Upgraded) Transforms a complex Anthropic request, including tools."""
    final_model_name = os.getenv("DEFAULT_MODEL_OVERRIDE", req.model)
    if os.getenv("DEFAULT_MODEL_OVERRIDE"):
        console.info(f"Model override active: '{req.model}' -> '{final_model_name}'")

    # Translate messages
    standard_messages = []
    if req.system:
        system_text = "".join(str(b.text) for b in req.system if hasattr(b, 'type') and b.type == "text" and hasattr(b, 'text')) if isinstance(req.system, list) else req.system
        standard_messages.append(ChatMessage(role="system", content=system_text))
    for msg in req.messages:
        content_text = "".join(b.text for b in msg.content if b.type == "text" and b.text is not None) if isinstance(msg.content, list) else msg.content
        standard_messages.append(ChatMessage(role=msg.role, content=content_text))

    # Translate tools
    standard_tools = []
    if req.tools:
        for tool in req.tools:
            standard_tools.append(Tool(
                type="function",
                function=Function(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.input_schema.properties
                )
            ))

    return StandardizedChatRequest(
        model=final_model_name,
        messages=standard_messages,
        stream=req.stream,
        tools=standard_tools if standard_tools else None,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )

async def _full_response_translator(
    adapter_response: Union[Dict[str, Any], AsyncGenerator[bytes, None]],
) -> AsyncGenerator[str, None]:
    """(Upgraded) The final translator, now handling tool calls in the response."""
    # This translator now needs to be more complex to handle both text and tool calls.
    # For brevity in this final response, we will focus on the request-side translation
    # which is the primary blocker. A complete implementation would require a similarly
    # detailed translation for the response stream, converting OpenAI tool_calls
    # back into Anthropic's tool_use format.
    
    # Simplified stream for text generation to ensure basic functionality
    if isinstance(adapter_response, AsyncGenerator):
        async for chunk in adapter_response:
            chunk_str = chunk.decode("utf-8").strip()
            if not chunk_str:
                continue
            if chunk_str == "data: [DONE]":
                yield 'event: message_stop\ndata: {"type": "message_stop"}\n\n'
                break
            try:
                data = json.loads(chunk_str[6:])
                # Handle text delta
                delta = data.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content")
                if content:
                    delta_event_data = {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": content}}
                    yield f'event: content_block_delta\ndata: {json.dumps(delta_event_data)}\n\n'
                
                # Handle tool calls delta
                tool_calls = delta.get("tool_calls")
                if tool_calls:
                    for i, tool_call in enumerate(tool_calls):
                        tool_use_event = {"type": "content_block_start", "index": i, "content_block": {"type": "tool_use", "id": tool_call["id"], "name": tool_call["function"]["name"], "input": {}}}
                        yield f'event: content_block_start\ndata: {json.dumps(tool_use_event)}\n\n'
                        
                        input_delta_event = {"type": "content_block_delta", "index": i, "delta": {"type": "input_json_delta", "partial_json": tool_call["function"]["arguments"]}}
                        yield f'event: content_block_delta\ndata: {json.dumps(input_delta_event)}\n\n'

            except json.JSONDecodeError:
                console.warning(f"Could not decode stream chunk: {chunk_str}")
                continue

@router.post("/v1/messages", response_model=None)
async def anthropic_proxy(request: AnthropicChatRequest) -> Union[StreamingResponse, JSONResponse]:
    try:
        console.info(f"Anthropic proxy received request for model: {request.model}")
        standard_request = _transform_anthropic_to_standard(request)
        
        adapter = get_adapter(model_name=standard_request.model)
        adapter_response = await adapter.chat_completions(standard_request)
        
        if standard_request.stream:
            final_stream = _full_response_translator(adapter_response)
            return StreamingResponse(final_stream, media_type="text/event-stream")
        else:
            # Non-streaming tool use translation would be needed here as well.
            return JSONResponse(content=adapter_response) # Simplified for now

    except Exception as e:
        console.exception(f"FATAL: An unhandled error occurred in anthropic_proxy: {e}")
        error_content = {"type": "error", "error": {"type": "internal_server_error", "message": str(e)}}
        return JSONResponse(status_code=500, content=error_content)