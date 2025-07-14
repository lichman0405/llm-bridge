# app/core/schemas.py
# The following code defines the schemas used in the LLM Bridge application.
# It includes the structure for chat messages, function definitions, and standardized API requests.
# Author: Shibo Li
# date: 2025-07-14
# Version 0.1.0

from pydantic import BaseModel
from typing import List, Dict, Optional, Union, Literal

# Basic chat message structure

class ChatMessage(BaseModel):
    """
    A single chat message in the conversation.
    This is used to represent both user and assistant messages.
    """
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None

# Function and tool definitions

class Function(BaseModel):
    """
    Defines the structure of a function (tool) that the model can call.
    """
    name: str
    description: Optional[str] = None
    parameters: Dict

class Tool(BaseModel):
    """
    Defines a tool that can be used in the conversation.
    Currently, only function types are supported.
    """
    type: Literal["function"] = "function"
    function: Function

class StandardizedChatRequest(BaseModel):
    """
    A standardized chat completion request format, fully aligned with OpenAI's API.
    This serves as the "common language" within our bridging application.
    """
    model: str
    messages: List[ChatMessage]
    stream: bool = False
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[Union[str, Dict]] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    max_tokens: Optional[int] = None

    class Config:
        # This configuration allows for the creation of model instances to ignore any extra fields
        # that are not defined in the model. This is useful for receiving requests from different clients
        # that may contain non-standard fields, increasing the robustness of our application.
        extra = "ignore"

# --- Standardized API Response Structure ---
# The response structure will be refined later when implementing adapters, as it needs to handle
# different models' return formats. For now, the request structure is the most critical part of
# launching the project.