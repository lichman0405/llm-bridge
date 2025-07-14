# app/adapters/openai_compatible.py
# The following code defines an adapter for OpenAI-compatible APIs.
# This adapter acts as a proxy, forwarding standardized requests to the target API endpoint.
# Author: Shibo Li
# date: 2025-07-14
# Version 0.1.0

import httpx
from typing import AsyncGenerator, Any, Dict, Union

from app.adapters.base import BaseAdapter
from app.core.schemas import StandardizedChatRequest
from app.core.logger import console

class OpenAICompatibleAdapter(BaseAdapter):
    """
    Adapter for OpenAI's API and other OpenAI-compatible services.
    """

    def __init__(self, api_key: str, base_url: str):
        super().__init__(api_key, base_url)

    async def _stream_response_generator(
        self, response: httpx.Response
    ) -> AsyncGenerator[bytes, None]:
        """A robust generator to stream the response and handle network errors."""
        try:
            async for chunk in response.aiter_bytes():
                yield chunk
        except httpx.ReadError as e:
            console.error(f"A network read error occurred while streaming the response: {e}")
            # This error is often due to the remote server closing the connection.
            # We can log it but stop yielding chunks gracefully.
        except Exception as e:
            console.error(f"An unexpected error occurred during streaming: {e}")
        finally:
            # Ensure the response is always closed.
            await response.aclose()

    async def chat_completions(
        self,
        request: StandardizedChatRequest,
    ) -> Union[Dict[str, Any], AsyncGenerator[bytes, None]]:
        """
        Forwards the chat completion request to an OpenAI-compatible API.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": request.model,
            "messages": [msg.dict(exclude_none=True) for msg in request.messages],
            "stream": request.stream,
        }

        async with httpx.AsyncClient() as client:
            api_url = f"{self.base_url}/chat/completions"
            req = client.build_request(
                "POST",
                api_url,
                headers=headers,
                json=payload,
                timeout=300
            )

            response = await client.send(req, stream=request.stream)
            
            if response.status_code != 200:
                error_body = await response.aread()
                console.error(f"Downstream API error ({response.status_code}): {error_body.decode()}")
            
            response.raise_for_status()

            if request.stream:
                # Use our new robust generator to handle the stream.
                return self._stream_response_generator(response)
            else:
                return response.json()