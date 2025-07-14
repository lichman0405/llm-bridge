# app/api/v1/endpoints/proxy.py

from fastapi import APIRouter, HTTPException, Request as FastAPIRequest
from fastapi.responses import StreamingResponse
from typing import Union

from app.core.schemas import StandardizedChatRequest, ChatMessage
from app.services.model_manager import get_adapter
from app.core.logger import console

# Create a new API router for our proxy endpoints.
router = APIRouter()

async def _extract_and_transform_request(
    model_name: str,
    fastapi_request: FastAPIRequest
) -> StandardizedChatRequest:
    """
    Extracts the request body and transforms it into our internal standard format.
    This is where we would handle any format differences if claude-code's
    requests were not OpenAI-compatible.
    """
    try:
        # Assuming the incoming request body is largely OpenAI-compatible.
        body = await fastapi_request.json()
        messages = [ChatMessage.parse_obj(msg) for msg in body.get("messages", [])]
        
        # Construct our standardized request object.
        return StandardizedChatRequest(
            model=model_name,
            messages=messages,
            stream=body.get("stream", False),
            # Pass through other potential parameters if they exist in the body
            temperature=body.get("temperature"),
            top_p=body.get("top_p"),
            max_tokens=body.get("max_tokens"),
        )
    except Exception as e:
        console.error(f"Failed to parse incoming request for model {model_name}: {e}")
        raise HTTPException(status_code=400, detail="Invalid request body format.")

@router.post("/bedrock-proxy/{model_name:path}")
async def bedrock_proxy(model_name: str, fastapi_request: FastAPIRequest) -> Union[dict, StreamingResponse]:
    """
    This endpoint mimics a Bedrock (or any other) service endpoint.
    It extracts the real model name from the URL path and processes the request.
    
    The '{model_name:path}' part allows the model name to contain slashes,
    which can be useful for some model naming schemes.
    """
    try:
        console.info(f"Proxy request received for model: {model_name}")

        # 1. Transform the incoming request into our internal standard format.
        standard_request = await _extract_and_transform_request(model_name, fastapi_request)

        # 2. Get the appropriate adapter using our model manager.
        adapter = get_adapter(model_name=standard_request.model)
        
        # 3. The rest of the logic is identical to our standard chat endpoint.
        if standard_request.stream:
            response = await adapter.chat_completions(standard_request)
            return StreamingResponse(response, media_type="text/event-stream")
        else:
            response = await adapter.chat_completions(standard_request)
            console.success(f"Successfully returned non-streaming proxy response for model: {model_name}")
            return response

    except ValueError as e:
        console.error(f"Proxy validation error for model {model_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        console.exception(f"An unexpected proxy error occurred for model {model_name}: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")