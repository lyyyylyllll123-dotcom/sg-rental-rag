"""
DeepSeek LLM Wrapper Module
Wrap DeepSeek API using LangChain ChatModel interface
"""
import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

# Import configuration
try:
    from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
except ImportError:
    # If config module doesn't exist, use environment variables
    DEEPSEEK_API_KEY = None
    DEEPSEEK_BASE_URL = None
    DEEPSEEK_MODEL = None


def get_deepseek_llm(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 2000,
) -> BaseChatModel:
    """
    Create DeepSeek LLM instance
    
    Args:
        api_key: DeepSeek API Key (priority: parameter > config > environment variable)
        base_url: API Base URL (priority: parameter > config > environment variable)
        model_name: Model name (priority: parameter > config > environment variable)
        temperature: Temperature parameter, default 0.3 (lower temperature ensures more accurate answers)
        max_tokens: Maximum generated tokens, default 2000
    
    Returns:
        LangChain ChatOpenAI instance (configured for DeepSeek API)
    
    Raises:
        ValueError: If API Key is not configured
    """
    # Priority: parameter > config module > environment variable > default value
    api_key = api_key or DEEPSEEK_API_KEY or os.getenv("OPENAI_API_KEY")
    base_url = base_url or DEEPSEEK_BASE_URL or os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    model_name = model_name or DEEPSEEK_MODEL or os.getenv("MODEL_NAME", "deepseek-chat")
    
    if not api_key:
        raise ValueError(
            "DeepSeek API Key is not configured. Please set the OPENAI_API_KEY environment variable or pass the api_key parameter when calling."
        )
    
    # Create ChatOpenAI instance, configured for DeepSeek API
    llm = ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        openai_api_base=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    return llm

