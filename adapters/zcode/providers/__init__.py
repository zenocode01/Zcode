"""LLM Provider：统一 chat 接口与工具调用三层降级。

- Provider 抽象 + OpenAI 兼容基座
- chat_with_tools / detect_tool_level：工具降级（L2 原生 / L1 提示词编码 / L0 无工具）
"""
from .base import Provider
from .openai_compat import OpenAICompatProvider
from .tool_fallback import chat_with_tools, detect_tool_level, parse_tool_call_l1

__all__ = [
    "Provider",
    "OpenAICompatProvider",
    "chat_with_tools",
    "detect_tool_level",
    "parse_tool_call_l1",
]
