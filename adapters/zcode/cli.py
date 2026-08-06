"""zcode CLI：profile / skills / platforms / workflow / metaskill / memory 子命令。

用法:
  zcode skills list
  zcode --profile <name> info
  zcode platforms list
  zcode workflow list
  zcode workflow run <name> [--dry-run]
  zcode metaskill list
  zcode metaskill run <name> [--dry-run]
  zcode memory add <内容> [--user <id>]
  zcode memory search <查询> [--user <id>] [--top-k N]
  zcode memory list [--user <id>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .profile import load_profile
from .workflow import WORKFLOWS_DIR, list_workflows, load_workflow, run_workflow
from .metaskill import (
    METASKILLS_DIR,
    list_metaskills,
    load_metaskill,
    run_metaskill,
)
from .providers import OpenAICompatProvider
from .handoff import save_handoff, load_handoff
from .evoskills import log_skill_use, audit_skill, print_audit
from .marketplace import build_marketplace, validate_all, write_marketplace, generate_claude_plugin, generate_opencode_config, generate_kimi_plugin

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"
PROFILES_DIR = REPO_ROOT / "adapters" / "profiles"
PLATFORMS_DIR = REPO_ROOT / "adapters" / "platforms"
ZCODE_CONFIG = Path.home() / ".zcode" / "config"


def _default_profile_name() -> str:
    """从 ~/.zcode/config 读默认 profile 名（install.sh 生成）。"""
    if ZCODE_CONFIG.exists():
        for line in ZCODE_CONFIG.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("default_profile"):
                return line.split("=", 1)[1].strip().strip('"')
    return "local-qwen3.6-35b"


def _load_default_profile():
    """加载默认 profile（metaskill 等需调用模型的命令使用）。"""
    name = _default_profile_name()
    return load_profile(PROFILES_DIR / f"{name}.yaml")


def _make_provider(profile):
    """从 profile 的 memory.llm 配置构造 OpenAI 兼容 Provider。"""
    llm = (profile.memory.llm if profile.memory else {}) or {}
    return OpenAICompatProvider(
        base_url=llm.get("base_url", "http://127.0.0.1:8080/v1"),
        model=llm.get("model", profile.model_family),
    )

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
    print(f"  编排模式: {p.orchestration}  (deterministic=确定性模板 / meta=模型自由编排)")
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


def cmd_metaskill_list(args: argparse.Namespace) -> int:
    """列出可用 MetaSkill。"""
    names = list_metaskills()
    if not names:
        print("（暂无 MetaSkill）")
        return 0
    for n in names:
        try:
            ms = load_metaskill(METASKILLS_DIR / f"{n}.yaml")
            print(f"{n}  {ms.description}")
        except (FileNotFoundError, ValueError) as e:
            print(f"{n}  [加载失败: {e}]")
    return 0


def cmd_metaskill_run(args: argparse.Namespace) -> int:
    """执行 MetaSkill：模型生成编排计划 → 复用确定性执行器。"""
    path = METASKILLS_DIR / f"{args.name}.yaml"
    try:
        ms = load_metaskill(path)
    except (FileNotFoundError, ValueError) as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    try:
        profile = _load_default_profile()
    except (FileNotFoundError, ValueError) as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    provider = _make_provider(profile)
    return run_metaskill(ms, provider, task=args.task or "", dry_run=args.dry_run)


def _load_memstore(args: argparse.Namespace):
    """加载默认 profile 并构造 MemStore（memory 子命令共用）。"""
    from .memory import MemStore

    profile = _load_default_profile()
    return MemStore(profile)


def cmd_memory_add(args: argparse.Namespace) -> int:
    store = _load_memstore(args)
    print(f"写入记忆（infer={store.infer_mode}）...")
    try:
        result = store.add(args.content, user_id=args.user)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    ids = result.get("results", []) if isinstance(result, dict) else []
    print(f"已写入 {len(ids)} 条记忆")
    for r in ids:
        print(f"  [{r.get('id')}] {r.get('memory', '')[:80]}")
    return 0


def _csv(values: str | None) -> list[str] | None:
    """逗号分隔字符串 → 列表（去空）。"""
    if values is None:
        return None
    return [v.strip() for v in values.split(",") if v.strip()]


def cmd_handoff_save(args: argparse.Namespace) -> int:
    path = save_handoff(
        project_dir=args.project,
        global_store=args.global_store,
        goal=args.goal or "",
        achieved=_csv(args.achieved),
        in_progress=_csv(args.in_progress),
        decisions=_csv(args.decisions),
        validation=_csv(args.validation),
        next_steps=_csv(args.next),
    )
    print(f"✓ 会话接力快照已保存: {path}")
    return 0


def cmd_handoff_load(args: argparse.Namespace) -> int:
    content = load_handoff(project_dir=args.project, global_store=args.global_store)
    if not content:
        print("（无会话接力快照；用 zcode handoff save 创建）")
        return 0
    print(content, end="")
    return 0


def cmd_tools(args: argparse.Namespace) -> int:
    """展示工具映射表（Layer 0：统一子代理接口 → 8 平台）。"""
    from .tool_mapping import TOOL_MAP

    print("工具映射表（统一子代理接口 → 各平台）：")
    for platform, tools in TOOL_MAP.items():
        print(f"  {platform}:")
        for key, value in tools.items():
            print(f"    {key:<9} {value}")
    return 0


def cmd_skill_log(args: argparse.Namespace) -> int:
    """捕获技能使用记录（EvoSkills 监控/捕获）。"""
    try:
        path = log_skill_use(args.name, args.result, lesson=args.lesson, context=args.context)
    except (FileNotFoundError, ValueError) as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    print(f"✓ 已记录技能使用: {path}")
    return 0


def cmd_skill_audit(args: argparse.Namespace) -> int:
    """评估技能健康度（EvoSkills 评估）。"""
    try:
        audit = audit_skill(args.name)
    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    print_audit(audit)
    return 0


def cmd_market_list(args: argparse.Namespace) -> int:
    """展示技能市场清单（含质量状态）。"""
    market = build_marketplace()
    print(f"技能市场: {market['interface']['displayName']} v{market['version']}（{market['count']} 个技能）")
    valid = 0
    for s in market["skills"]:
        mark = "✓" if s["valid"] else "⚠"
        valid += 1 if s["valid"] else 0
        print(f"  {mark} {s['name']}  {s['description'][:50]}")
    print(f"质量: {valid}/{market['count']} 通过校验")
    return 0


def cmd_market_validate(args: argparse.Namespace) -> int:
    """全量质量校验。"""
    results = validate_all()
    all_ok = True
    for name, issues in results.items():
        if issues:
            all_ok = False
            print(f"⚠ {name}:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print(f"✓ {name}")
    print("== 全部通过 ==" if all_ok else f"== 有 {sum(1 for i in results.values() if i)} 个技能存在问题 ==")
    return 0 if all_ok else 1


def cmd_market_generate(args: argparse.Namespace) -> int:
    """生成平台深度插件文件。"""
    platform = args.platform
    if platform == "claude-code":
        path = generate_claude_plugin()
        print(f"✓ Claude Code 插件已生成: {path}/marketplace.json + plugin.json")
    elif platform == "opencode":
        print(json.dumps(generate_opencode_config(), ensure_ascii=False, indent=2))
        print("\n（把以上内容合并进 ~/.config/opencode/opencode.json 的顶层）")
    elif platform == "kimi-code":
        print(json.dumps(generate_kimi_plugin(), ensure_ascii=False, indent=2))
        print("\n（把以上内容合并进 ~/.kimi-code/plugins/installed.json）")
    else:
        print(f"不支持的平台: {platform}（支持: claude-code / opencode / kimi-code）", file=sys.stderr)
        return 1
    return 0


def cmd_memory_search(args: argparse.Namespace) -> int:
    store = _load_memstore(args)
    try:
        results = store.search(args.query, user_id=args.user, top_k=args.top_k)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    if not results:
        print("（无匹配记忆）")
        return 0
    print(f"检索到 {len(results)} 条：")
    for r in results:
        print(f"  [{r['id']}] (score={r.get('score', '?'):.3f}) {r['memory'][:100]}")
    return 0


def cmd_memory_list(args: argparse.Namespace) -> int:
    store = _load_memstore(args)
    try:
        results = store.get_all(user_id=args.user)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    if not results:
        print("（暂无记忆）")
        return 0
    print(f"共 {len(results)} 条记忆：")
    for r in results:
        print(f"  [{r['id']}] {r['memory'][:100]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="zcode",
        description="Zcode 技能运行时：跨平台技能安装与本地模型适配",
    )
    parser.add_argument(
        "--profile", "-p", default=None,
        help="profile 名称（用于 info 子命令，如 local-qwen3.6-35b）",
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

    sp_meta = sub.add_parser("metaskill", help="MetaSkill 自由编排（Layer 2）")
    meta_sub = sp_meta.add_subparsers(dest="metaskill_command", required=True)
    meta_sub.add_parser("list", help="列出 MetaSkill").set_defaults(func=cmd_metaskill_list)
    sp_ms_run = meta_sub.add_parser("run", help="执行 MetaSkill（模型编排）")
    sp_ms_run.add_argument("name", help="MetaSkill 名（如 feature-dev）")
    sp_ms_run.add_argument("--task", default="", help="任务描述（可选，覆盖 when）")
    sp_ms_run.add_argument("--dry-run", action="store_true", help="只生成编排提示，不调用模型")
    sp_ms_run.set_defaults(func=cmd_metaskill_run)

    sp_memory = sub.add_parser("memory", help="记忆层（Layer 3，mem0 本地三件套）")
    mem_sub = sp_memory.add_subparsers(dest="memory_command", required=True)
    sp_mem_add = mem_sub.add_parser("add", help="写入记忆")
    sp_mem_add.add_argument("content", help="记忆内容（文本/对话）")
    sp_mem_add.add_argument("--user", default="default", help="用户/会话 ID")
    sp_mem_add.set_defaults(func=cmd_memory_add)
    sp_mem_search = mem_sub.add_parser("search", help="检索记忆")
    sp_mem_search.add_argument("query", help="查询文本")
    sp_mem_search.add_argument("--user", default="default")
    sp_mem_search.add_argument("--top-k", type=int, default=5)
    sp_mem_search.set_defaults(func=cmd_memory_search)
    sp_mem_list = mem_sub.add_parser("list", help="列出记忆")
    sp_mem_list.add_argument("--user", default="default")
    sp_mem_list.set_defaults(func=cmd_memory_list)

    sp_handoff = sub.add_parser("handoff", help="会话接力（Layer 3）")
    ho_sub = sp_handoff.add_subparsers(dest="handoff_command", required=True)
    sp_ho_save = ho_sub.add_parser("save", help="保存接力快照（会话结束时）")
    sp_ho_save.add_argument("--goal", default="", help="当前目标")
    sp_ho_save.add_argument("--achieved", default="", help="已完成（逗号分隔）")
    sp_ho_save.add_argument("--in-progress", default="", help="进行中（逗号分隔）")
    sp_ho_save.add_argument("--decisions", default="", help="决策记录（逗号分隔）")
    sp_ho_save.add_argument("--validation", default="", help="验证结果（逗号分隔）")
    sp_ho_save.add_argument("--next", default="", help="下一步建议（逗号分隔）")
    sp_ho_save.add_argument("--project", default=None, help="项目目录（默认当前目录）")
    sp_ho_save.add_argument("--global", dest="global_store", action="store_true", help="存全局 ~/.zcode/handoff.md")
    sp_ho_save.set_defaults(func=cmd_handoff_save)
    sp_ho_load = ho_sub.add_parser("load", help="读取接力快照（会话开始时）")
    sp_ho_load.add_argument("--project", default=None)
    sp_ho_load.add_argument("--global", dest="global_store", action="store_true")
    sp_ho_load.set_defaults(func=cmd_handoff_load)

    sp_tools = sub.add_parser("tools", help="工具映射表（Layer 0）")
    sp_tools.add_argument("list", nargs="?")
    sp_tools.set_defaults(func=cmd_tools)

    sp_skill = sub.add_parser("skill", help="技能自我迭代（EvoSkills, Layer 3）")
    sk_sub = sp_skill.add_subparsers(dest="skill_command", required=True)
    sp_sk_log = sk_sub.add_parser("log", help="记录技能使用（捕获）")
    sp_sk_log.add_argument("name", help="技能名（如 tdd）")
    sp_sk_log.add_argument("result", choices=["成功", "失败", "改进"], help="使用结果")
    sp_sk_log.add_argument("--lesson", default="", help="一句话教训")
    sp_sk_log.add_argument("--context", default="", help="使用场景")
    sp_sk_log.set_defaults(func=cmd_skill_log)
    sp_sk_audit = sk_sub.add_parser("audit", help="评估技能健康度")
    sp_sk_audit.add_argument("name", help="技能名")
    sp_sk_audit.set_defaults(func=cmd_skill_audit)

    sp_market = sub.add_parser("market", help="技能市场与质量评估（Phase 4）")
    mkt_sub = sp_market.add_subparsers(dest="market_command", required=True)
    mkt_sub.add_parser("list", help="市场清单（含质量状态）").set_defaults(func=cmd_market_list)
    mkt_sub.add_parser("validate", help="全量质量校验").set_defaults(func=cmd_market_validate)
    sp_mkt_gen = mkt_sub.add_parser("generate", help="生成平台深度插件")
    sp_mkt_gen.add_argument("platform", choices=["claude-code", "opencode", "kimi-code"])
    sp_mkt_gen.set_defaults(func=cmd_market_generate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
