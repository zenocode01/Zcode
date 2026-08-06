"""profile 加载与校验。

Profile 是"能力声明"：context_window / tool_level / json_reliability 等字段
决定技能版本（SKILL.md / SKILL.local.md）与记忆策略的加载。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

REQUIRED_FIELDS = ("name", "model_family", "context_window", "tool_level")


@dataclass
class MemoryConfig:
    """记忆层本地三件套配置（Phase 3 接入 mem0）。"""

    llm: dict = field(default_factory=dict)
    embedder: dict | None = None
    vector_store: dict | None = None
    infer_mode: str = "simplified"
    write_frequency: str = "low"


@dataclass
class Profile:
    """本地模型能力声明。"""

    name: str
    model_family: str
    context_window: int
    tool_level: int
    json_reliability: str = "low"
    skill_variant: str = "local"
    memory: MemoryConfig | None = None
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        missing = [f for f in REQUIRED_FIELDS if f not in data]
        if missing:
            raise ValueError(f"profile 缺少必填字段: {', '.join(missing)}")

        memory = None
        if "memory" in data:
            mem = data["memory"] or {}
            memory = MemoryConfig(
                llm=mem.get("llm", {}),
                embedder=mem.get("embedder"),
                vector_store=mem.get("vector_store"),
                infer_mode=mem.get("infer_mode", "simplified"),
                write_frequency=mem.get("write_frequency", "low"),
            )

        known = {"name", "model_family", "context_window", "tool_level",
                 "json_reliability", "skill_variant", "memory"}
        extra = {k: v for k, v in data.items() if k not in known}

        return cls(
            name=data["name"],
            model_family=data["model_family"],
            context_window=int(data["context_window"]),
            tool_level=int(data["tool_level"]),
            json_reliability=data.get("json_reliability", "low"),
            skill_variant=data.get("skill_variant", "local"),
            memory=memory,
            extra=extra,
        )


def load_profile(path: str | Path) -> Profile:
    """从 YAML 文件加载 profile，校验必填字段。"""
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"profile 文件不存在: {p}")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"profile 格式错误（应为 YAML 映射）: {p}")
    return Profile.from_dict(data)
