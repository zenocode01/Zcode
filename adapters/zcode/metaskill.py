"""MetaSkill 自由编排引擎（Layer 2）。

与确定性模板（workflow.py）相对：把"可用技能 + 编排规则"交给模型，
由模型生成步骤计划（model-orchestrated），再复用确定性执行器执行。

流程: 加载 MetaSkill → 构造编排提示 → 模型输出计划 → 解析 → 执行
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .workflow import REPO_ROOT, Step, Workflow, run_workflow

SKILLS_DIR = REPO_ROOT / "skills"
METASKILLS_DIR = REPO_ROOT / "metaskills"

# 模型编排计划输出格式：`N. skill: <名>` / `N. prompt: <文本>` / `N. command: <命令>`
_PLAN_LINE_RE = re.compile(r"^\s*\d+\.\s*(?P<kind>skill|prompt|command)\s*:\s*(?P<value>.+?)\s*$")


@dataclass
class MetaSkill:
    name: str
    description: str
    when: str = ""
    skills: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "MetaSkill":
        if "name" not in data or "skills" not in data:
            raise ValueError("MetaSkill 必须含 name 与 skills 字段")
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            when=data.get("when", ""),
            skills=data["skills"],
            rules=data.get("rules", []),
        )


def load_metaskill(path: str | Path) -> MetaSkill:
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"MetaSkill 文件不存在: {p}")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"MetaSkill 格式错误（应为 YAML 映射）: {p}")
    return MetaSkill.from_dict(data)


def list_metaskills() -> list[str]:
    if not METASKILLS_DIR.exists():
        return []
    return sorted(p.stem for p in METASKILLS_DIR.glob("*.yaml") if not p.name.startswith("_"))


def _skill_catalog(skill_names: list[str]) -> str:
    """从 skills/ 读取各技能的 frontmatter description 构造技能目录。"""
    lines = []
    for name in skill_names:
        for f in (SKILLS_DIR / name / "SKILL.md", SKILLS_DIR / name / "SKILL.local.md"):
            if f.exists():
                text = f.read_text(encoding="utf-8")
                desc = ""
                m = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
                if m:
                    desc = m.group(1).strip()
                lines.append(f"- {name}: {desc}")
                break
        else:
            raise FileNotFoundError(f"技能 {name} 不存在于 skills/ 目录")
    return "\n".join(lines)


def build_orchestration_prompt(ms: MetaSkill, task: str = "") -> str:
    """构造给模型的编排提示。"""
    catalog = _skill_catalog(ms.skills)
    rules = "\n".join(f"- {r}" for r in ms.rules) or "- 无额外规则"
    goal = task or ms.when or ms.description
    return (
        "你是工作流编排器。根据目标，在可用技能中编排一个执行计划。\n\n"
        f"【目标】\n{goal}\n\n"
        f"【可用技能】\n{catalog}\n\n"
        f"【编排规则（必须遵守）】\n{rules}\n\n"
        "【输出格式】每行一个步骤，编号从 1 开始，只输出计划：\n"
        "1. skill: <技能名>\n"
        "2. prompt: <该步对执行者的说明>\n"
        "不要输出其他内容。"
    )


def parse_orchestration(text: str) -> list[Step]:
    """解析模型输出的编排计划为步骤列表。"""
    steps: list[Step] = []
    for line in text.splitlines():
        m = _PLAN_LINE_RE.match(line)
        if not m:
            continue
        kind = m.group("kind")
        value = m.group("value")
        if kind == "skill":
            steps.append(Step(kind="skill", value=value))
        elif kind == "prompt":
            steps.append(Step(kind="prompt", value=value))
        else:  # command
            steps.append(Step(kind="command", value=value))
    if not steps:
        raise ValueError("模型未输出可解析的编排计划（无 'N. skill:/prompt:' 行）")
    return steps


def run_metaskill(
    ms: MetaSkill,
    provider,
    task: str = "",
    dry_run: bool = False,
) -> int:
    """执行 MetaSkill：模型生成计划 → 复用确定性执行器。

    :param provider: LLM Provider（生成编排计划用）
    :param dry_run: 只生成并打印计划，不执行 command 步骤
    """
    prompt = build_orchestration_prompt(ms, task)
    print(f"== MetaSkill: {ms.name} — {ms.description} ==")
    print("【编排提示】")
    print(prompt)
    print()

    if dry_run:
        print("（dry-run：未调用模型，跳过编排生成与执行）")
        return 0

    try:
        plan_text = provider.chat([{"role": "user", "content": prompt}])
    except ConnectionError as e:
        print(f"错误: {e}", )
        return 1

    print("【模型编排计划】")
    print(plan_text)
    print()

    try:
        steps = parse_orchestration(plan_text)
    except ValueError as e:
        print(f"错误: {e}", )
        return 1

    wf = Workflow(name=ms.name, description=ms.description + "（MetaSkill 编排）", steps=steps)
    return run_workflow(wf, dry_run=dry_run)
