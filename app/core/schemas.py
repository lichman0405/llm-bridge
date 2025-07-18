# app/core/schemas.py
# The following code defines the schemas used in the LLM Bridge application.
# It includes the structure for chat messages, function definitions, and standardized API requests.
# Author: Shibo Li
# date: 2025-07-14
# Version 0.1.0


from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Optional, Union, Literal, Any

# --- OpenAI Compatible Schemas (Internal Standard) ---

class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None

class Function(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Dict

class Tool(BaseModel):
    type: Literal["function"] = "function"
    function: Function

class StandardizedChatRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    model: str
    messages: List[ChatMessage]
    stream: bool = False
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[Union[str, Dict]] = None
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None

# --- Anthropic API Specific Schemas (UPGRADED for Tool Use) ---

class AnthropicToolInputSchema(BaseModel):
    type: str = "object"
    properties: Dict[str, Any]
    required: Optional[List[str]] = None

class AnthropicTool(BaseModel):
    name: str
    description: str
    input_schema: AnthropicToolInputSchema

class AnthropicContentBlock(BaseModel):
    type: str
    text: Optional[str] = None
    # For tool use requests from the model
    id: Optional[str] = None
    name: Optional[str] = None
    input: Optional[Dict] = None

class AnthropicMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: Union[str, List[AnthropicContentBlock]]

class AnthropicChatRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    model: str
    messages: List[AnthropicMessage]
    system: Optional[Union[str, List[AnthropicContentBlock]]] = None
    max_tokens: int
    stream: bool = False
    temperature: Optional[float] = None
    tools: Optional[List[AnthropicTool]] = None