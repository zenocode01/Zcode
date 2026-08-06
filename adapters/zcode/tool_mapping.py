"""工具映射表（Layer 0）：统一子代理/任务接口 → 各平台实现。

subagent-driven-development 技能依赖宿主提供子代理能力。
本模块把"统一接口"映射到 8 平台的实际工具，供技能与 CLI 查询。
接口:
  spawn    — 派一个子代理执行任务（独立上下文）
  parallel — 并行派多个子代理
  todo     — 任务清单跟踪
  review   — 派审查子代理
"""
from __future__ import annotations

# 依据各平台官方能力整理；"无原生"表示需降级（多实例/外部编排/单代理串行）
TOOL_MAP: dict[str, dict[str, str]] = {
    "kimi-code": {
        "spawn": "Agent 工具（explore/coder/plan 子代理，独立上下文）",
        "parallel": "AgentSwarm（同模板多子代理并行）",
        "todo": "TodoList（内置）",
        "review": "Agent（派 coder 子代理 + code-reviewer 模板）",
    },
    "claude-code": {
        "spawn": "Task 工具（子代理，独立上下文）",
        "parallel": "Task 多实例并行",
        "todo": "TodoWrite 工具",
        "review": "Task（+ code-reviewer 模板）",
    },
    "codex": {
        "spawn": "spawn_agent（非阻塞子代理）",
        "parallel": "多 spawn_agent 并行",
        "todo": "update_plan",
        "review": "spawn_agent（+ code-reviewer 模板）",
    },
    "opencode": {
        "spawn": "opencode run 子命令 / agent 插件",
        "parallel": "多 opencode run 实例",
        "todo": "todo 文件（opencode.json 配置）",
        "review": "opencode run（+ code-reviewer 模板）",
    },
    "cursor": {
        "spawn": "Agent 面板（人工触发，无 API 子代理）",
        "parallel": "无原生并行（IDE 限制）",
        "todo": "手工 / 项目文件",
        "review": "Agent 面板（+ code-reviewer 模板）",
    },
    "gemini-cli": {
        "spawn": "无原生子代理 API（可用多 CLI 实例）",
        "parallel": "多实例并行",
        "todo": "内置 task 跟踪",
        "review": "gemini 新会话（+ code-reviewer 模板）",
    },
    "pi": {
        "spawn": "无原生子代理（pi 为极简 harness）",
        "parallel": "无",
        "todo": "无",
        "review": "新 pi 会话（+ code-reviewer 模板）",
    },
    "reasonix": {
        "spawn": "无原生子代理（终端 agent）",
        "parallel": "无",
        "todo": "reasonix 配置/文件",
        "review": "新会话（+ code-reviewer 模板）",
    },
}

# 降级说明：无原生子代理的平台，subagent-driven-development 降级为
# 单代理串行（executing-plans 模式）或外部编排（zcode workflow 驱动）


def tools_for(platform: str) -> dict[str, str]:
    """查询某平台的工具映射。"""
    return TOOL_MAP.get(platform, {})
