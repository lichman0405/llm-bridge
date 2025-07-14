# app/api/v1/endpoints/chat.py
# This module defines the chat completions endpoint for our API.
# It handles requests for chat completions, manages the interaction with the model adapters,
# and returns the appropriate responses, either as a stream or a standard JSON response.
# Author: Shibo Li
# Date: 2025-07-14
# Version: 0.1.0

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Union, Dict, Any

from app.core.schemas import StandardizedChatRequest
from app.services.model_manager import get_adapter
from app.core.logger import console

router = APIRouter()


@router.post("/chat/completions", response_model=None)
async def chat_completions(request: StandardizedChatRequest) -> Union[Dict[str, Any], StreamingResponse]:
    """
    Main endpoint for handling chat completion requests.

    It orchestrates the process:
    1. Logs the incoming request.
    2. Selects the appropriate adapter based on the model name.
    3. Calls the adapter to process the request to the downstream LLM API.
    4. Returns either a streaming or a standard JSON response.
    5. Handles potential errors gracefully.
    """
    try:
        console.info(f"Received chat completion request for model: {request.model}")

        adapter = get_adapter(model_name=request.model)

        response = await adapter.chat_completions(request)

        if request.stream:
            return StreamingResponse(response, media_type="text/event-stream")
        else:
            if isinstance(response, dict):
                console.success(f"Successfully returned non-streaming response for model: {request.model}")
                return response
            else:
                raise ValueError("Adapter returned unexpected response type for non-streaming request")

    except ValueError as e:
        console.error(f"Validation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        console.exception(f"An unexpected error occurred for model {request.model}: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")