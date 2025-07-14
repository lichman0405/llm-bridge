# app/adapters/base.py
# The following ocde defines the abstract base class for all Large Language Model (LLM) adapters.
# This class serves as a contract for implementing specific LLM adapters, ensuring they can be used
# interchangeably by the application's services.
# Author: Shibo Li
# date: 2025-07-14
# Version 0.1.0

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any, Dict, Union, Optional

from app.core.schemas import StandardizedChatRequest


class BaseAdapter(ABC):
    """
    Abstract Base Class (Interface) for all Large Language Model adapters.

    This class defines a common contract that all concrete adapters must follow,
    ensuring they can be used interchangeably by the application's services.
    """

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        Initializes the adapter with necessary credentials and settings.

        Args:
            api_key (str): The API key for the LLM service.
            base_url (str, optional): The base URL for the API endpoint.
                                      Defaults to None, as some clients (like Anthropic's)
                                      do not require it during initialization.
        """
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def chat_completions(
        self,
        request: StandardizedChatRequest,
    ) -> Union[Dict[str, Any], AsyncGenerator[bytes, None]]:
        """
        The core method to handle chat completion requests.

        This method must be implemented by all concrete adapter subclasses. It is
        responsible for translating the standardized request, sending it to the
        target LLM API, and transforming the response back into a standardized
        format or a byte stream.

        Args:
            request: A standardized chat request object.

        Returns:
            If request.stream is False, it returns a dictionary representing the
            complete, non-streaming JSON response.
            If request.stream is True, it returns an asynchronous generator that
            yields bytes corresponding to Server-Sent Events (SSE).
        """
        pass