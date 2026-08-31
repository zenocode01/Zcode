"""OpenAI 兼容 Provider：对接 llama.cpp server（/v1）等本地端点。

无需第三方 SDK，仅用标准库 urllib，适合轻量运行环境。
端点未启动时抛出 ConnectionError，提示启动命令（可离线演示）。
"""
from __future__ import annotations

import json
import urllib.request

from .base import Provider


class OpenAICompatProvider(Provider):
    name = "openai-compat"

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080/v1",
        model: str = "qwen3.6-27b",
        timeout: float = 120.0,
        default_max_tokens: int = 4096,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        # 推理模型（Qwen3 系 think 模式）思考会消耗大量 token，默认给足预算
        self.default_max_tokens = default_max_tokens

    def _endpoint_available(self) -> bool:
        """探测本地端点是否在运行（GET /models 健康检查）。"""
        try:
            req = urllib.request.Request(self.base_url + "/models", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _post(self, payload: dict) -> dict:
        """发送 chat/completions 请求，返回完整响应。"""
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def chat_message(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> dict:
        """发送消息，返回完整 assistant message（含 content / reasoning_content / tool_calls）。

        工具调用场景必须用本方法（content 可能为空，tool_calls 承载结果）。
        """
        if not self._endpoint_available():
            raise ConnectionError(
                f"未检测到本地端点 {self.base_url}（llama.cpp server 是否已启动？）。\n"
                f"启动示例: llama-server -m qwen3.6-35b.gguf --ctx-size 262144 --port 6001"
            )

        payload: dict = {"model": self.model, "messages": messages, **kwargs}
        payload.setdefault("max_tokens", self.default_max_tokens)
        if tools:
            payload["tools"] = tools

        result = self._post(payload)
        return result["choices"][0]["message"]

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> str:
        msg = self.chat_message(messages, tools=tools, **kwargs)
        content = msg.get("content", "")
        # 推理模型：思考占满预算时 content 可能为空，降级返回 reasoning_content
        if not content and msg.get("reasoning_content"):
            return msg["reasoning_content"]
        return content
