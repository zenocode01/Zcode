"""LLM Provider 抽象基类。"""
from __future__ import annotations

from abc import ABC, abstractmethod


class Provider(ABC):
    """所有本地/远程 LLM 提供方的统一接口。"""

    name: str = "base"

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> str:
        """发送消息，返回模型回复文本。

        :param messages: OpenAI 兼容消息列表（role/content）
        :param tools: 可选工具定义（OpenAI 兼容格式）
        """
