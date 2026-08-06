"""工具调用三层降级（草案 §四.2）。

小模型工具调用弱的表现：不遵循 schema、一次只调一个工具、参数错、幻觉工具名。
对策分三层，按模型能力自动选择:

  L2 原生 tool calling: 模型声明支持 tools → 直接透传 OpenAI 兼容 tools 格式
  L1 提示词编码: 要求输出 <tool>名称</tool><args>JSON</args>，解析器提取
  L0 无工具模式: 模型只输出"走哪条分支"的决策，外部 runner 执行命令
"""
from __future__ import annotations

import json
import re

# L1 编码格式
_TOOL_TEMPLATE = (
    "【可用工具】\n"
    "{tools_text}\n"
    "需要调用工具时，输出格式（只输出这一行）：\n"
    "<tool>工具名</tool><args>{\"参数\": \"值\"}</args>\n"
    "不需要工具时，直接输出回答文本。"
)

_TOOL_CALL_RE = re.compile(
    r"<tool>(?P<name>[^<]+)</tool>\s*<args>(?P<args>.*?)</args>",
    re.DOTALL,
)


def _format_tools_l1(tools: list[dict]) -> str:
    lines = []
    for t in tools:
        name = t.get("function", {}).get("name", "?")
        desc = t.get("function", {}).get("description", "")
        params = t.get("function", {}).get("parameters", {})
        required = params.get("required", [])
        props = params.get("properties", {})
        arg_hint = ", ".join(f"{k}({props[k].get('type', '?')})" for k in props) or "无参数"
        lines.append(f"- {name}: {desc} 参数: {arg_hint} 必填: {required or '无'}")
    return "\n".join(lines)


def encode_tools_l1(tools: list[dict]) -> str:
    """把工具定义编码为提示词文本（L1）。"""
    return _TOOL_TEMPLATE.format(tools_text=_format_tools_l1(tools))


def parse_tool_call_l1(text: str) -> list[dict] | None:
    """从模型输出解析 <tool>...</tool><args>...</args> 调用。

    返回 [{name, arguments}]；未找到调用返回 None；args 解析失败时 arguments 为原始字符串。
    """
    matches = list(_TOOL_CALL_RE.finditer(text))
    if not matches:
        return None
    calls = []
    for m in matches:
        args_raw = m.group("args").strip()
        try:
            arguments = json.loads(args_raw) if args_raw else {}
        except json.JSONDecodeError:
            arguments = args_raw  # 保留原文，由调用方容错
        calls.append({"name": m.group("name").strip(), "arguments": arguments})
    return calls


def chat_with_tools(
    provider,
    messages: list[dict],
    tools: list[dict] | None = None,
    tool_level: int = 1,
) -> dict:
    """按工具级别路由一次对话。

    返回 {"text": ..., "tool_calls": [...] | None, "tool_level": int}
    """
    tools = tools or []
    if tool_level >= 2 and tools:
        # L2: 原生 tool calling 透传（模型支持与否由探测决定）
        text = provider.chat(messages, tools=tools)
        return {"text": text, "tool_calls": None, "tool_level": 2}

    if tool_level == 1 and tools:
        # L1: 提示词编码 + 解析
        encoded = encode_tools_l1(tools)
        prompt_messages = list(messages)
        prompt_messages[-1] = {
            "role": messages[-1]["role"],
            "content": messages[-1].get("content", "") + "\n\n" + encoded,
        }
        text = provider.chat(prompt_messages)
        calls = parse_tool_call_l1(text)
        return {"text": text, "tool_calls": calls, "tool_level": 1}

    # L0: 无工具模式（或未给工具）——模型只输出决策文本，由外部 runner 解释执行
    text = provider.chat(messages)
    return {"text": text, "tool_calls": None, "tool_level": 0}


def detect_tool_level(provider, model_hint: str = "") -> int:
    """探测模型工具调用能力（一次性小基准）。

    让模型调用一个"返回 42"的测试工具；能按 L1 格式输出 → 1；
    模型家族含 qwen/glm 且声称支持 tool call → 建议 2（需实测）；其余 → 0。
    端点不可用时返回 -1。
    """
    if not hasattr(provider, "_endpoint_available") or not provider._endpoint_available():
        return -1

    probe_tools = [{
        "type": "function",
        "function": {
            "name": "get_answer",
            "description": "返回数字 42",
            "parameters": {"type": "object", "properties": {}},
        },
    }]
    probe_messages = [{"role": "user", "content": "请调用 get_answer 工具。"}]
    try:
        result = chat_with_tools(provider, probe_messages, probe_tools, tool_level=1)
        if result["tool_calls"]:
            return 1
        text = result["text"].lower()
        # 模型回复了 42 但没走格式 → 弱工具；原生 tool calling 需 L2 测试
        if "42" in text:
            # 家族提示：qwen/glm 系列本地版通常支持原生 tools
            if any(k in model_hint.lower() for k in ("qwen", "glm")):
                return 2
            return 1
        return 0
    except Exception:
        return 0
