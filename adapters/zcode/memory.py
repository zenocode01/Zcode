"""MemStore — 统一记忆接口（Layer 3）。

路线：先 mem0 后自建（见 docs/开发偏好与默认配置.md）。
本模块是统一抽象边界：add/search/update/delete 内部用 mem0 实现，
将来自建替换时只改本模块，接口不变。

配置来源：profile.memory（llm / embedder / vector_store / infer_mode）。
"""
from __future__ import annotations

from pathlib import Path

from .profile import Profile

# 注册自定义 HTTP Embedder（llama.cpp /embedding 端点，非 OpenAI 兼容）
from mem0.utils.factory import EmbedderFactory

EmbedderFactory.provider_to_class["zcode_http"] = "zcode.http_embedder.HttpEmbedder"

# 简化提取提示词（L1）：面向本地小模型，只做"事实提取 + 分类"，砍掉
# linked_memory_ids、相对时间锚定等重要求（对应草案 §2.2）
# 注意：mem0 提取 pipeline 期望 JSON object（含 memory 数组），必须保持此结构
SIMPLIFIED_PROMPT = (
    "从上述内容中提取值得长期记忆的事实。"
    "只输出 JSON，格式为 {\"memory\": [{\"text\": \"记忆内容\", \"category\": \"user_preference|decision|lesson|其他\"}]}。"
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
        provider = emb.get("provider", "zcode_http")
        model = emb.get("model", "Qwen3-Embedding-8B")
        dims = int(emb.get("dims", 0) or 4096)
        base_url = emb.get("base_url", "http://127.0.0.1:8088")

        if provider in ("openai", "zcode_http"):
            # llama.cpp /embedding 端点（自定义 provider，复用 openai_base_url 字段）
            return (
                {"provider": "zcode_http", "config": {
                    "model": model,
                    "openai_base_url": base_url,
                }},
                dims,
            )
        # fastembed（本地库，无网络依赖时可作备用）
        return ({"provider": "fastembed", "config": {"model": model}}, dims)

    def _build_mem0(self):
        from mem0 import Memory  # 延迟导入，避免未安装时拖垮 CLI
        from mem0.configs.base import MemoryConfig
        from mem0.embeddings.configs import EmbedderConfig
        from mem0.llms.configs import LlmConfig
        from mem0.vector_stores.configs import VectorStoreConfig

        embedder_cfg, dims = self._embedder_config()
        vs = (self.profile.memory.vector_store if self.profile.memory else {}) or {}
        llm_cfg = self._llm_config()

        config = MemoryConfig(
            llm=LlmConfig(provider=llm_cfg["provider"], config=llm_cfg["config"]),
            # model_construct 跳过 provider 白名单校验（zcode_http 为自定义 provider）
            embedder=EmbedderConfig.model_construct(
                provider=embedder_cfg["provider"],
                config=embedder_cfg["config"],
            ),
            vector_store=VectorStoreConfig(
                provider=vs.get("provider", "qdrant"),
                config={
                    "path": vs.get("path", "~/.zcode/memory"),
                    "embedding_model_dims": dims,
                },
            ),
            history_db_path="~/.zcode/memory/history.db",
        )
        return Memory(config=config)

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
        result = self._mem.search(
            query,
            filters={"user_id": user_id},
            top_k=top_k,
        )
        results = result.get("results", []) if isinstance(result, dict) else []
        return [{
            "id": r.get("id"),
            "memory": r.get("memory"),
            "score": r.get("score"),
        } for r in results]

    def get_all(self, user_id: str = "default", top_k: int = 50) -> list[dict]:
        result = self._mem.get_all(filters={"user_id": user_id}, top_k=top_k)
        results = result.get("results", []) if isinstance(result, dict) else []
        return [{"id": r.get("id"), "memory": r.get("memory")} for r in results]

    def delete(self, memory_id: str) -> dict:
        return self._mem.delete(memory_id)

    def update(self, memory_id: str, content: str) -> dict:
        return self._mem.update(memory_id, content)
