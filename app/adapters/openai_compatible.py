# app/adapters/openai_compatible.py
# The following code defines an adapter for OpenAI-compatible APIs.
# This adapter acts as a proxy, forwarding standardized requests to the target API endpoint.
# Author: Shibo Li
# date: 2025-07-14
# Version 0.1.0

# app/adapters/openai_compatible.py

import httpx
from typing import AsyncGenerator, Any, Dict, Union
from app.adapters.base import BaseAdapter
from app.core.schemas import StandardizedChatRequest
from app.core.logger import console

class OpenAICompatibleAdapter(BaseAdapter):
    """Adapter for OpenAI's API and other OpenAI-compatible services."""

    def __init__(self, api_key: str, base_url: str):
        super().__init__(api_key, base_url)

    async def chat_completions(
        self,
        request: StandardizedChatRequest,
    ) -> Union[Dict[str, Any], AsyncGenerator[bytes, None]]:
        """Forwards the chat completion request, now including tools."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # Build a payload that now includes tools if they exist.
        payload = {
            "model": request.model,
            "messages": [msg.dict(exclude_none=True) for msg in request.messages],
            "stream": request.stream,
        }
        if request.tools:
            payload["tools"] = [t.dict() for t in request.tools]
        if request.tool_choice:
            payload["tool_choice"] = request.tool_choice
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        
        timeout_config = httpx.Timeout(300.0, connect=60.0)
        api_url = f"{self.base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=timeout_config) as client:
            try:
                if request.stream:
                    async with client.stream("POST", api_url, headers=headers, json=payload) as response:
                        response.raise_for_status()
                        async def generator():
                            async for chunk in response.aiter_bytes():
                                yield chunk
                        return generator()
                else:
                    response = await client.post(api_url, headers=headers, json=payload)
                    response.raise_for_status()
                    return response.json()
            
            except httpx.HTTPStatusError as e:
                error_body = await e.response.aread()
                console.error(f"Downstream API error ({e.response.status_code}): {error_body.decode()}")
                raise