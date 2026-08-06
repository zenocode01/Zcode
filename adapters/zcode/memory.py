"""MemStore — 统一记忆接口（Layer 3）。

路线：先 mem0 后自建（见 docs/开发偏好与默认配置.md）。
本模块是统一抽象边界：add/search/update/delete 内部用 mem0 实现，
将来自建替换时只改本模块，接口不变。

配置来源：profile.memory（llm / embedder / vector_store / infer_mode）。
"""
from __future__ import annotations

from pathlib import Path

from .profile import Profile

# 简化提取提示词（L1）：面向本地小模型，只做"事实提取 + 分类"，砍掉
# linked_memory_ids、相对时间锚定等重要求（对应草案 §2.2）
SIMPLIFIED_PROMPT = (
    "从以下内容中提取值得长期记忆的事实。"
    "只输出 JSON 数组，每项包含 text（记忆内容）和 category（user_preference/decision/lesson/其他）。"
    "不要输出其他内容。"
)


class MemStore:
    """统一记忆接口（mem0 实现）。"""

    def __init__(self, profile: Profile):
        self.profile = profile
        self.infer_mode = (profile.memory.infer_mode if profile.memory else "simplified")
        self._mem = self._build_mem0()

    # ---- 配置 ----

    def _llm_config(self) -> dict:
        llm = (self.profile.memory.llm if self.profile.memory else {}) or {}
        base_url = llm.get("base_url", "http://127.0.0.1:8080/v1")
        model = llm.get("model", self.profile.model_family)
        return {"provider": "openai", "config": {
            "model": model,
            "openai_base_url": base_url,
            "api_key": "local",  # llama.cpp 本地端点不校验 key
        }}

    def _embedder_config(self) -> tuple[dict, int]:
        """返回 (embedder 配置, embedding 维度)。"""
        emb = (self.profile.memory.embedder if self.profile.memory else {}) or {}
        provider = emb.get("provider", "fastembed")
        model = emb.get("model", "BAAI/bge-small-en-v1.5")
        dims = int(emb.get("dims", 0) or 384)

        if provider == "openai":
            # llama.cpp --embeddings 端点（OpenAI 兼容）
            return (
                {"provider": "openai", "config": {
                    "model": model,
                    "openai_base_url": emb.get("base_url", "http://127.0.0.1:8080/v1"),
                    "api_key": "local",
                }},
                dims,
            )
        # fastembed（本地库，验证/轻量场景）
        return ({"provider": "fastembed", "config": {"model": model}}, dims)

    def _build_mem0(self):
        from mem0 import Memory  # 延迟导入，避免未安装时拖垮 CLI

        embedder_cfg, dims = self._embedder_config()
        vs = (self.profile.memory.vector_store if self.profile.memory else {}) or {}
        vector_store_cfg = {
            "provider": vs.get("provider", "qdrant"),
            "config": {
                "path": vs.get("path", "~/.zcode/memory"),
                "embedding_model_dims": dims,
            },
        }
        config = {
            "llm": self._llm_config(),
            "embedder": embedder_cfg,
            "vector_store": vector_store_cfg,
            "history_db_path": "~/.zcode/memory/history.db",
        }
        return Memory.from_config(config)

    # ---- 统一接口 ----

    def add(
        self,
        content: str,
        user_id: str = "default",
        metadata: dict | None = None,
    ) -> dict:
        """写入记忆。

        infer_mode:
          - none/skip  → infer=False（L0：纯 embedding，零 LLM）
          - simplified → infer=True + 简化提取提示词（L1，默认）
        """
        infer = self.infer_mode not in ("none", "skip", "off")
        prompt = SIMPLIFIED_PROMPT if (infer and self.infer_mode == "simplified") else None
        return self._mem.add(
            content,
            user_id=user_id,
            metadata=metadata,
            infer=infer,
            prompt=prompt,
        )

    def search(self, query: str, user_id: str = "default", top_k: int = 5) -> list[dict]:
        """检索记忆（mem0 v2 检索零 LLM：embedding + 混合打分）。"""
        result = self._mem.search(query, user_id=user_id, top_k=top_k)
        results = result.get("results", []) if isinstance(result, dict) else []
        return [{
            "id": r.get("id"),
            "memory": r.get("memory"),
            "score": r.get("score"),
        } for r in results]

    def get_all(self, user_id: str = "default", top_k: int = 50) -> list[dict]:
        result = self._mem.get_all(user_id=user_id, top_k=top_k)
        results = result.get("results", []) if isinstance(result, dict) else []
        return [{"id": r.get("id"), "memory": r.get("memory")} for r in results]

    def delete(self, memory_id: str) -> dict:
        return self._mem.delete(memory_id)

    def update(self, memory_id: str, content: str) -> dict:
        return self._mem.update(memory_id, content)
