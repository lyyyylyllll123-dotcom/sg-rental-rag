"""
DeepSeek LLM 封装模块
使用 LangChain ChatModel 接口封装 DeepSeek API
"""
import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

# 导入配置
try:
    from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
except ImportError:
    # 如果 config 模块不存在，使用环境变量
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
    创建 DeepSeek LLM 实例
    
    Args:
        api_key: DeepSeek API Key（优先使用参数，其次 config，最后环境变量）
        base_url: API Base URL（优先使用参数，其次 config，最后环境变量）
        model_name: 模型名称（优先使用参数，其次 config，最后环境变量）
        temperature: 温度参数，默认 0.3（较低温度保证更准确的回答）
        max_tokens: 最大生成 token 数，默认 2000
    
    Returns:
        LangChain ChatOpenAI 实例（配置为 DeepSeek API）
    
    Raises:
        ValueError: 如果 API Key 未配置
    """
    # 优先级：参数 > config 模块 > 环境变量 > 默认值
    api_key = api_key or DEEPSEEK_API_KEY or os.getenv("OPENAI_API_KEY")
    base_url = base_url or DEEPSEEK_BASE_URL or os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    model_name = model_name or DEEPSEEK_MODEL or os.getenv("MODEL_NAME", "deepseek-chat")
    
    if not api_key:
        raise ValueError(
            "DeepSeek API Key 未配置。请设置环境变量 OPENAI_API_KEY 或在调用时传入 api_key 参数。"
        )
    
    # 创建 ChatOpenAI 实例，配置为 DeepSeek API
    llm = ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        openai_api_base=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    return llm

