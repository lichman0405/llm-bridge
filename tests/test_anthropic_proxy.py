# tests/test_anthropic_proxy.py

import json
import pytest
from typing import AsyncGenerator
from app.core.schemas import AnthropicChatRequest, AnthropicMessage, StandardizedChatRequest
from app.api.v1.endpoints.anthropic_proxy import _transform_anthropic_to_standard, _openai_to_anthropic_stream_translator

# 1. Define a test case
def test_transform_anthropic_to_standard_with_system_prompt():
    """
    Tests if the transformation correctly handles a request
    that includes a system prompt.
    """
    # 2. Prepare input data (Arrange)
    # Simulate a request from claude-code
    anthropic_request = AnthropicChatRequest(
        model="deepseek-chat",
        messages=[
            AnthropicMessage(role="user", content="Hello, world!")
        ],
        system="You are a helpful assistant.",
        max_tokens=1024,
        stream=True
    )

    # 3. Execute the function under test (Act)
    standard_request = _transform_anthropic_to_standard(anthropic_request)

    # 4. Assert the results meet expectations (Assert)
    # Check if the return is the expected internal standard request type
    assert isinstance(standard_request, StandardizedChatRequest)
    # Check if the model name is correctly passed
    assert standard_request.model == "deepseek-chat"
    # Check if the message list length is correct (system prompt + user message)
    assert len(standard_request.messages) == 2
    # Check if the first message is the correct system prompt
    assert standard_request.messages[0].role == "system"
    assert standard_request.messages[0].content == "You are a helpful assistant."
    # Check if the second message is the correct user message
    assert standard_request.messages[1].role == "user"
    assert standard_request.messages[1].content == "Hello, world!"
    # Check if other parameters are correctly passed
    assert standard_request.stream is True
    assert standard_request.max_tokens == 1024

def test_transform_anthropic_to_standard_without_system_prompt():
    """
    Tests if the transformation works correctly for requests
    without a system prompt.
    """
    # Prepare input data
    anthropic_request = AnthropicChatRequest(
        model="gpt-4o",
        messages=[
            AnthropicMessage(role="user", content="First message."),
            AnthropicMessage(role="assistant", content="First response."),
            AnthropicMessage(role="user", content="Second message.")
        ],
        max_tokens=500,
        stream=False
    )

    # Execute function
    standard_request = _transform_anthropic_to_standard(anthropic_request)

    # Assert results
    assert len(standard_request.messages) == 3
    assert standard_request.messages[0].role == "user"
    assert standard_request.messages[1].role == "assistant"
    assert standard_request.messages[2].role == "user"
    assert standard_request.stream is False
    assert standard_request.max_tokens == 500


async def mock_openai_stream() -> AsyncGenerator[bytes, None]:
    """A mock async generator that yields OpenAI-style SSE chunks."""
    chunks = [
        'data: {"choices": [{"delta": {"content": "Hello"}}]}\n\n',
        'data: {"choices": [{"delta": {"content": ", "}}]}\n\n',
        'data: {"choices": [{"delta": {"content": "world!"}}]}\n\n',
        'data: [DONE]\n\n'
    ]
    for chunk in chunks:
        yield chunk.encode('utf-8')

# 2. Write an async test function since we are dealing with an async generator
@pytest.mark.asyncio
async def test_openai_to_anthropic_stream_translator():
    """
    Tests if the stream translator correctly converts OpenAI SSE events
    to Anthropic SSE events.
    """
    # 3. Prepare input data (Arrange)
    openai_stream = mock_openai_stream()

    # 4. Execute the function under test (Act)
    # Collect the results of the translated async generator into a list
    translated_chunks = [
        chunk async for chunk in _openai_to_anthropic_stream_translator(openai_stream)
    ]

    # 5. Assert the results meet expectations (Assert)
    # Check if the total number of generated data chunks is correct (3 content chunks + 1 end chunk)
    assert len(translated_chunks) == 4

    # Check the first content chunk
    first_chunk = translated_chunks[0]
    assert first_chunk.startswith("event: content_block_delta")
    first_data = json.loads(first_chunk.split("data: ")[1])
    assert first_data["type"] == "content_block_delta"
    assert first_data["delta"]["text"] == "Hello"

    # Check the second content chunk
    second_chunk = translated_chunks[1]
    second_data = json.loads(second_chunk.split("data: ")[1])
    assert second_data["delta"]["text"] == ", "

    # Check the third content chunk
    third_chunk = translated_chunks[2]
    third_data = json.loads(third_chunk.split("data: ")[1])
    assert third_data["delta"]["text"] == "world!"

    # Check the last end chunk
    last_chunk = translated_chunks[3]
    assert last_chunk.startswith("event: message_stop")
    last_data = json.loads(last_chunk.split("data: ")[1])
    assert last_data["type"] == "message_stop"