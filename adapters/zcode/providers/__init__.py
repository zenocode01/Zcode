"""LLM Provider：统一 chat 接口。

tools 参数为可选的工具定义列表（OpenAI 兼容格式）。
工具调用三层降级（L1 原生 tool calling / L2 提示词编码 / L3 无工具）在后续迭代实现，
本模块只定义接口与 OpenAI 兼容基座。
"""
from .base import Provider
from .openai_compat import OpenAICompatProvider

__all__ = ["Provider", "OpenAICompatProvider"]
