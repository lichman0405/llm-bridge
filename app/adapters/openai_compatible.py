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
            
            # 增加更详细的错误日志，方便未来调试
            if response.status_code != 200:
                error_body = await response.aread()
                console.error(f"Downstream API error ({response.status_code}): {error_body.decode()}")
            
            response.raise_for_status()

            if request.stream:
                return response.aiter_bytes()
            else:
                return response.json()