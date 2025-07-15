# app/adapters/base.py
# The following ocde defines the abstract base class for all Large Language Model (LLM) adapters.
# This class serves as a contract for implementing specific LLM adapters, ensuring they can be used
# interchangeably by the application's services.
# Author: Shibo Li
# date: 2025-07-14
# Version 0.1.0


from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any, Dict, Union

from app.core.schemas import StandardizedChatRequest


class BaseAdapter(ABC):
    """
    Abstract Base Class (Interface) for all Large Language Model adapters.
    """

    def __init__(self, api_key: str, base_url: str | None = None):
        """
        Initializes the adapter with necessary credentials and settings.
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
        """
        pass