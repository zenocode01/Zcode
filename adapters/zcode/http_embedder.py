"""自定义 HTTP Embedder：对接 llama.cpp /embedding 端点（Qwen3-Embedding-8B）。

端点格式（非 OpenAI 兼容）：
  POST {base_url}/embedding
  {"input": "文本" | ["文本1", ...], "normalize": true}
  响应: [{"index": 0, "embedding": [[v1, ...]]}, {"index": 1, "embedding": [[v2, ...]]}]
  —— 每个输入一个顶层元素，每项 embedding 为嵌套数组（取 [0] 为向量）

通过 mem0 EmbedderFactory.provider_to_class 注册为自定义 provider（zcode_http）。
"""
from __future__ import annotations

import json
import urllib.request
from typing import Literal, Optional

from mem0.configs.embeddings.base import BaseEmbedderConfig
from mem0.embeddings.base import EmbeddingBase


class HttpEmbedder(EmbeddingBase):
    def __init__(self, config: Optional[BaseEmbedderConfig] = None):
        super().__init__(config)
        self.config.model = self.config.model or "Qwen3-Embedding-8B"
        # 复用 openai_base_url 字段承载端点地址
        self.config.openai_base_url = self.config.openai_base_url or "http://127.0.0.1:8088"
        self.base_url = self.config.openai_base_url.rstrip("/")

    @staticmethod
    def _extract_vector(item: dict) -> list[float]:
        """从响应项提取向量：嵌套 [[v]] 取 [0]，平铺 [v] 直接用。"""
        emb = item.get("embedding")
        if not emb:
            raise ValueError(f"embedding 响应项缺少向量: {str(item)[:200]}")
        if isinstance(emb[0], list):
            return emb[0]
        return emb

    def _post(self, texts: list[str]) -> list[list[float]]:
        payload = json.dumps({"input": texts, "normalize": True}).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/embedding",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if not isinstance(data, list) or not data:
            raise ValueError(f"embedding 响应格式异常: {str(data)[:200]}")
        sorted_data = sorted(data, key=lambda x: x.get("index", 0))
        return [self._extract_vector(item) for item in sorted_data]

    def embed(self, text: str, memory_action: Optional[Literal["add", "search", "update"]] = None) -> list[float]:
        text = text.replace("\n", " ")
        return self._post([text])[0]

    def embed_batch(self, texts: list[str], memory_action: str = "add") -> list[list[float]]:
        if not texts:
            return []
        cleaned = [t.replace("\n", " ") for t in texts]
        vectors = self._post(cleaned)
        if len(vectors) != len(texts):
            raise ValueError(
                f"embed_batch 返回 {len(vectors)} 个向量，期望 {len(texts)} 个"
            )
        return vectors
