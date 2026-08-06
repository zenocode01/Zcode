"""会话接力（agent-handoff，Layer 3）。

在会话之间建立连续性记忆：当前目标 / 已完成 / 进行中 / 决策 / 验证结果 / 下一步，
让未来 Agent 恢复上下文，不依赖历史聊天记录。

存储：项目内 `.memory/handoff.md`（随项目走，本地数据不入库）；
      `--global` 时存 `~/.zcode/handoff.md`（跨项目）。
回写模板化：字段由调用方提供，不消耗模型 token。
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

GLOBAL_HANDOFF = Path.home() / ".zcode" / "handoff.md"


def _handoff_path(project_dir: str | Path | None, global_store: bool) -> Path:
    if global_store:
        return GLOBAL_HANDOFF
    base = Path(project_dir).expanduser() if project_dir else Path.cwd()
    return base / ".memory" / "handoff.md"


def _section(title: str, lines: list[str]) -> str:
    if not lines:
        return f"## {title}\n（空）\n\n"
    body = "\n".join(f"- {ln}" for ln in lines)
    return f"## {title}\n{body}\n\n"


def save_handoff(
    project_dir: str | Path | None = None,
    global_store: bool = False,
    goal: str = "",
    achieved: list[str] | None = None,
    in_progress: list[str] | None = None,
    decisions: list[str] | None = None,
    validation: list[str] | None = None,
    next_steps: list[str] | None = None,
) -> Path:
    """模板化生成/更新 handoff 快照。返回写入路径。"""
    path = _handoff_path(project_dir, global_store)
    path.parent.mkdir(parents=True, exist_ok=True)

    content = (
        "# 会话接力快照（agent-handoff）\n\n"
        f"- 更新时间: {datetime.now().isoformat(timespec='seconds')}\n"
        f"- 项目: {path.parent.parent if not global_store else '（全局）'}\n\n"
        + _section("当前目标", [goal] if goal else [])
        + _section("已完成", achieved or [])
        + _section("进行中", in_progress or [])
        + _section("决策记录", decisions or [])
        + _section("验证结果", validation or [])
        + _section("下一步建议", next_steps or [])
    )
    path.write_text(content, encoding="utf-8")
    return path


def load_handoff(project_dir: str | Path | None = None, global_store: bool = False) -> str:
    """读取 handoff 快照内容；不存在返回空字符串。"""
    path = _handoff_path(project_dir, global_store)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
