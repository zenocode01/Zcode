"""zcode CLI：profile / skills / platforms / workflow 子命令。

用法:
  zcode skills list
  zcode --profile <name> info
  zcode platforms list
  zcode workflow list
  zcode workflow run <name> [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .profile import load_profile
from .workflow import WORKFLOWS_DIR, list_workflows, load_workflow, run_workflow

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"
PROFILES_DIR = REPO_ROOT / "adapters" / "profiles"
PLATFORMS_DIR = REPO_ROOT / "adapters" / "platforms"

# 8 平台技能目录（与 install.sh 保持一致；路径依据调查报告确认）
PLATFORMS = {
    "claude-code": ["~/.claude/skills"],
    "cursor": ["~/.cursor/skills"],
    "codex": ["~/.codex/skills"],
    "gemini-cli": ["~/.gemini/skills"],
    "opencode": ["~/.config/opencode/skills"],
    "kimi-code": ["~/.kimi-code/skills"],
    "pi": ["~/.pi/agent/skills"],
    "reasonix": ["~/.reasonix/skills"],
}


def cmd_skills(args: argparse.Namespace) -> int:
    """列出技能库中的技能。"""
    if not SKILLS_DIR.exists():
        print(f"错误: skills/ 目录不存在（{SKILLS_DIR}）", file=sys.stderr)
        return 1
    names = sorted(
        d.name for d in SKILLS_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    )
    if not names:
        print("（暂无技能）")
        return 0
    for n in names:
        has_local = (SKILLS_DIR / n / "SKILL.local.md").exists()
        print(f"{n}  {'[有本地精简版]' if has_local else ''}")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """查看 profile 能力信息。"""
    if not args.profile:
        print("用法: zcode --profile <name> info", file=sys.stderr)
        return 1
    path = PROFILES_DIR / f"{args.profile}.yaml"
    try:
        p = load_profile(path)
    except (FileNotFoundError, ValueError) as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1

    print(f"profile: {p.name}")
    print(f"  模型家族: {p.model_family}")
    print(f"  上下文窗口: {p.context_window}")
    print(f"  工具级别: {p.tool_level}  (0=无工具 1=提示词编码 2=原生 tool calling)")
    print(f"  JSON 可靠性: {p.json_reliability}")
    print(f"  技能版本: {p.skill_variant}")
    if p.memory:
        llm = p.memory.llm
        vs = p.memory.vector_store or {}
        emb = p.memory.embedder or {}
        print(f"  记忆: LLM={llm.get('provider')}/{llm.get('model')}"
              f"  向量库={vs.get('provider')}{'@' + vs.get('path', '') if vs.get('path') else ''}"
              f"  写入={p.memory.infer_mode}/{p.memory.write_frequency}")
        if emb.get("provider") in (None, "<待定>"):
            print("  记忆: Embedding=未确定（待选型）")
        else:
            print(f"  记忆: Embedding={emb.get('provider')}/{emb.get('model')}")
    return 0


def cmd_platforms(args: argparse.Namespace) -> int:
    """列出 8 平台技能目录支持状态。"""
    print("平台技能目录支持状态（已存在=✓ 未安装=·）：")
    for name, dirs in PLATFORMS.items():
        statuses = []
        for d in dirs:
            path = Path(d).expanduser()
            statuses.append(f"{d} {'✓' if path.exists() else '·'}")
        print(f"  {name:<12} {' / '.join(statuses)}")
    return 0


def cmd_workflow_list(args: argparse.Namespace) -> int:
    """列出可用工作流。"""
    names = list_workflows()
    if not names:
        print("（暂无工作流）")
        return 0
    for n in names:
        try:
            wf = load_workflow(WORKFLOWS_DIR / f"{n}.yaml")
            print(f"{n}  {wf.description}")
        except (FileNotFoundError, ValueError) as e:
            print(f"{n}  [加载失败: {e}]")
    return 0


def cmd_workflow_run(args: argparse.Namespace) -> int:
    """执行工作流（--dry-run 只打印计划）。"""
    path = WORKFLOWS_DIR / f"{args.name}.yaml"
    try:
        wf = load_workflow(path)
    except (FileNotFoundError, ValueError) as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    return run_workflow(wf, dry_run=args.dry_run)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="zcode",
        description="Zcode 技能运行时：跨平台技能安装与本地模型适配",
    )
    parser.add_argument(
        "--profile", "-p", default=None,
        help="profile 名称（用于 info 子命令，如 local-qwen3.6-27b）",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sp_skills = sub.add_parser("skills", help="列出技能库")
    sp_skills.add_argument("list", nargs="?")
    sp_skills.set_defaults(func=cmd_skills)

    sp_platforms = sub.add_parser("platforms", help="列出平台技能目录状态")
    sp_platforms.add_argument("list", nargs="?")
    sp_platforms.set_defaults(func=cmd_platforms)

    sp_info = sub.add_parser("info", help="查看 profile 能力（需 --profile）")
    sp_info.set_defaults(func=cmd_info)

    sp_workflow = sub.add_parser("workflow", help="确定性工作流（Layer 2）")
    wf_sub = sp_workflow.add_subparsers(dest="workflow_command", required=True)
    wf_sub.add_parser("list", help="列出工作流").set_defaults(func=cmd_workflow_list)
    sp_wf_run = wf_sub.add_parser("run", help="执行工作流")
    sp_wf_run.add_argument("name", help="工作流名（如 feature-dev）")
    sp_wf_run.add_argument("--dry-run", action="store_true", help="只打印步骤计划，不执行命令")
    sp_wf_run.set_defaults(func=cmd_workflow_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
