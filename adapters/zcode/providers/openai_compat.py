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
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _endpoint_available(self) -> bool:
        """探测本地端点是否在运行（GET /models 健康检查）。"""
        try:
            req = urllib.request.Request(self.base_url + "/models", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> str:
        if not self._endpoint_available():
            raise ConnectionError(
                f"未检测到本地端点 {self.base_url}（llama.cpp server 是否已启动？）。\n"
                f"启动示例: llama-server -m qwen3.6-27b.gguf --ctx-size 262144 --port 8080"
            )

        payload: dict = {"model": self.model, "messages": messages, **kwargs}
        if tools:
            payload["tools"] = tools

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"]
