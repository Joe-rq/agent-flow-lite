"""
DeepSeek LLM client wrapper.
Provides chat completion with streaming support.
"""

from typing import AsyncGenerator

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionChunk

from .config import settings


def get_client() -> AsyncOpenAI:
    """
    Get or create the DeepSeek client instance.
    
    Returns:
        AsyncOpenAI: Configured async OpenAI client for DeepSeek
    """
    s = settings()
    return AsyncOpenAI(
        api_key=s.deepseek_api_key,
        base_url=s.deepseek_api_base,
    )


async def chat_completion(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """
    Send a chat completion request to DeepSeek API.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys.
                  Example: [{"role": "user", "content": "Hello!"}]
        model: Optional model name override. Uses deepseek_model from config if not provided.
        temperature: Sampling temperature (0.0 - 2.0). Lower = more deterministic.
        max_tokens: Maximum number of tokens to generate.
    
    Returns:
        str: The assistant's response content.
    
    Raises:
        ValueError: If API key is not configured.
        Exception: If API call fails.
    """
    s = settings()
    
    if not s.deepseek_api_key:
        raise ValueError(
            "DeepSeek API key not configured. "
            "Please set DEEPSEEK_API_KEY in your .env file."
        )
    
    client = get_client()
    target_model = model or s.deepseek_model
    
    try:
        response = await client.chat.completions.create(
            model=target_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content
        
        raise ValueError("Empty response from DeepSeek API")
    
    except Exception as e:
        raise Exception(f"DeepSeek API call failed: {str(e)}")


async def chat_completion_stream(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.7,
) -> AsyncGenerator[str, None]:
    """
    Stream chat completion from DeepSeek API.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys.
        model: Optional model name override.
        temperature: Sampling temperature (0.0 - 2.0).
    
    Yields:
        str: Chunks of the assistant's response content.
    
    Raises:
        ValueError: If API key is not configured.
    """
    s = settings()
    
    if not s.deepseek_api_key:
        raise ValueError(
            "DeepSeek API key not configured. "
            "Please set DEEPSEEK_API_KEY in your .env file."
        )
    
    client = get_client()
    target_model = model or s.deepseek_model
    
    try:
        stream = await client.chat.completions.create(
            model=target_model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    except Exception as e:
        raise Exception(f"DeepSeek streaming failed: {str(e)}")
