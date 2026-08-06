"""确定性工作流引擎（Layer 2，本地小模型模式）。

不依赖模型自由编排：工作流是显式线性步骤 + 条件分支，由本模块顺序驱动。
步骤类型:
  - skill:   加载 skills/<name>/SKILL[.local].md 作为指令
  - prompt:  原样给模型的提示词
  - command: 由 runner 直接执行的 shell 命令
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"
WORKFLOWS_DIR = REPO_ROOT / "workflows"


@dataclass
class Step:
    kind: str  # skill | prompt | command
    value: str
    when: str = "true"
    prompt: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Step":
        """从 YAML 步骤构造；支持 skill/prompt/command 三种键。"""
        if "skill" in data:
            return cls(kind="skill", value=data["skill"], when=str(data.get("when", "true")), prompt=data.get("prompt", ""))
        if "prompt" in data:
            return cls(kind="prompt", value=data["prompt"], when=str(data.get("when", "true")))
        if "command" in data:
            return cls(kind="command", value=data["command"], when=str(data.get("when", "true")))
        raise ValueError(f"步骤必须含 skill/prompt/command 之一: {data}")


@dataclass
class Workflow:
    name: str
    description: str
    steps: list[Step] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Workflow":
        if "name" not in data or "steps" not in data:
            raise ValueError("工作流必须含 name 与 steps 字段")
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            steps=[Step.from_dict(s) for s in data["steps"]],
        )


def load_workflow(path: str | Path) -> Workflow:
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"工作流文件不存在: {p}")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"工作流格式错误（应为 YAML 映射）: {p}")
    return Workflow.from_dict(data)


def list_workflows() -> list[str]:
    if not WORKFLOWS_DIR.exists():
        return []
    return sorted(p.stem for p in WORKFLOWS_DIR.glob("*.yaml") if not p.name.startswith("_"))


def _skill_instruction(skill_name: str, skill_variant: str = "local") -> str:
    """按 profile 技能版本加载技能文件内容作为指令。"""
    variants = ([skill_variant] if skill_variant in ("local", "standard") else ["local"])
    for v in variants:
        suffix = ".local" if v == "local" else ""
        f = SKILLS_DIR / skill_name / f"SKILL{suffix}.md"
        if f.exists():
            return f.read_text(encoding="utf-8")
    # 兜底：任一版本
    for f in (SKILLS_DIR / skill_name / "SKILL.md", SKILLS_DIR / skill_name / "SKILL.local.md"):
        if f.exists():
            return f.read_text(encoding="utf-8")
    raise FileNotFoundError(f"技能 {skill_name} 不存在于 skills/ 目录")


def _condition_ok(when: str, variables: dict) -> bool:
    """显式条件判断：true/false 或 ${var} 占位（由调用方提供）。"""
    w = when.strip()
    if w == "true":
        return True
    if w == "false":
        return False
    if w.startswith("${") and w.endswith("}"):
        key = w[2:-1]
        return bool(variables.get(key, False))
    return bool(variables.get(w, False))


def plan_workflow(wf: Workflow, variables: dict | None = None, skill_variant: str = "local") -> list[dict]:
    """展开工作流为可执行步骤计划（不实际执行）。"""
    variables = variables or {}
    plan = []
    for i, step in enumerate(wf.steps, 1):
        if not _condition_ok(step.when, variables):
            plan.append({"index": i, "kind": step.kind, "skipped": True, "why": f"条件不满足: {step.when}"})
            continue
        if step.kind == "skill":
            plan.append({
                "index": i, "kind": "skill", "skill": step.value,
                "instruction": _skill_instruction(step.value, skill_variant),
                "prompt": step.prompt or "",
            })
        elif step.kind == "prompt":
            plan.append({"index": i, "kind": "prompt", "instruction": step.value})
        else:  # command
            plan.append({"index": i, "kind": "command", "instruction": step.value})
    return plan


def run_workflow(wf: Workflow, variables: dict | None = None, skill_variant: str = "local", dry_run: bool = False) -> int:
    """执行工作流。dry_run=True 只打印计划不执行 command。

    返回 0 成功；command 步骤失败返回非 0。
    """
    plan = plan_workflow(wf, variables, skill_variant)
    print(f"== 工作流: {wf.name} — {wf.description} ==")
    for item in plan:
        if item.get("skipped"):
            print(f"  [{item['index']}] (跳过) {item['why']}")
            continue
        print(f"  [{item['index']}] [{item['kind']}] {item.get('skill', item.get('instruction', ''))[:60]}")
        if item["kind"] == "command" and not dry_run:
            print(f"    $ {item['instruction']}")
            result = subprocess.run(item["instruction"], shell=True)
            if result.returncode != 0:
                print(f"    命令失败 (exit={result.returncode})", )
                return result.returncode
    return 0
