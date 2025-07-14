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


class OpenAICompatibleAdapter(BaseAdapter):
    """
    Adapter for OpenAI's API and other OpenAI-compatible services.

    This adapter acts primarily as a proxy, forwarding the standardized
    request to the target API endpoint without significant modification,
    as our internal standard is based on OpenAI's format.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        """
        Initializes the adapter for OpenAI-compatible APIs.

        Args:
            api_key (str): The API key for the service.
            base_url (str): The base URL of the API endpoint.
                            Defaults to OpenAI's official URL.
        """
        super().__init__(api_key, base_url)

    async def chat_completions(
        self,
        request: StandardizedChatRequest,
    ) -> Union[Dict[str, Any], AsyncGenerator[bytes, None]]:
        """
        Forwards the chat completion request to an OpenAI-compatible API.

        It uses the httpx library to make an asynchronous POST request.
        It handles both streaming and non-streaming responses based on the
        'stream' flag in the request.

        Args:
            request: A standardized chat request object.

        Returns:
            - A dictionary with the full JSON response if stream is False.
            - An async generator yielding bytes for SSE if stream is True.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = request.dict(exclude_none=True)

        async with httpx.AsyncClient() as client:
            api_url = f"{self.base_url}/chat/completions"
            req = client.build_request(
                "POST",
                api_url,
                headers=headers,
                json=payload,
                timeout=1500 
            )


            response = await client.send(req, stream=request.stream)
            response.raise_for_status() 

            if request.stream:
                async def stream_generator():
                    async for chunk in response.aiter_bytes():
                        yield chunk
                return stream_generator()
            else:
                return response.json()