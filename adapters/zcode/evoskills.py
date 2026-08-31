"""EvoSkills 自我迭代引擎（Layer 3）。

循环：监控 → 捕获 → 评估 → 迭代 → 验证 → 发布
- 监控/捕获: log_skill_use() 把每次技能使用写入 skills/<name>/.memory/experience.log（模板化）
- 评估:     audit_skill() 读 experience.log + improvements.md，统计成功率与改进建议，
            给出健康评分与发布建议
- 迭代/验证/发布: 由 Agent 按 skills/evoskills 技能指导执行（读建议→重写 SKILL.md→
            软链已指向仓库自动生效）

experience.log 行格式: <日期> | <场景> | <结果:成功/失败/改进> | <一句话教训>
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"

# 发布阈值：成功率低于此值或未处理改进建议达此数 → 建议生成改进版本
SUCCESS_RATE_THRESHOLD = 0.7
IMPROVEMENTS_THRESHOLD = 2

_LOG_LINE_RE = re.compile(r"^\s*(?P<date>\S+)\s*\|\s*(?P<context>.*?)\s*\|\s*(?P<result>成功|失败|改进)\s*\|\s*(?P<lesson>.*?)\s*$")


@dataclass
class SkillAudit:
    skill: str
    total: int = 0
    results: Counter = field(default_factory=Counter)  # 成功/失败/改进
    lessons: list[str] = field(default_factory=list)   # 失败/改进的教训
    improvements: list[str] = field(default_factory=list)  # 未处理改进建议
    success_rate: float = 0.0
    needs_revision: bool = False
    revision_published: bool = False  # 技能文件在最近失败/改进后已修改（修订版已发布）

    @property
    def summary(self) -> str:
        r = self.results
        return (f"使用 {self.total} 次（成功 {r.get('成功', 0)} / 失败 {r.get('失败', 0)}"
                f" / 改进 {r.get('改进', 0)}），成功率 {self.success_rate:.0%}，"
                f"未处理改进建议 {len(self.improvements)} 条")


def _skill_dir(skill_name: str) -> Path:
    d = SKILLS_DIR / skill_name
    if not d.exists():
        raise FileNotFoundError(f"技能 {skill_name} 不存在于 skills/ 目录")
    return d


def log_skill_use(
    skill_name: str,
    result: str,
    lesson: str = "",
    context: str = "",
    date: str | None = None,
) -> Path:
    """捕获一次技能使用记录（追加到 .memory/experience.log）。

    result: 成功 / 失败 / 改进
    """
    if result not in ("成功", "失败", "改进"):
        raise ValueError("result 必须为 成功/失败/改进 之一")
    d = _skill_dir(skill_name)
    mem_dir = d / ".memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    path = mem_dir / "experience.log"
    stamp = date or datetime.now().strftime("%Y-%m-%d")
    line = f"{stamp} | {context} | {result} | {lesson}"
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    return path


def _read_improvements(skill_name: str) -> list[str]:
    """读取 improvements.md 中未勾选（- [ ]）的改进建议。"""
    path = SKILLS_DIR / skill_name / ".memory" / "improvements.md"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("- [ ]"):
            out.append(line.strip()[5:].strip())
    return out


def _revision_published_since_last_issue(skill_dir: Path, log_path: Path) -> bool:
    """技能文件是否在最近一次失败/改进记录之后被修改过（即已发布修订版）。

    用于审计闭环：发布修订版后，不再仅因历史成功率建议修订，改为等待新样本。
    无法判定（无技能文件 / 无记录 / 日期解析失败）时返回 False，退化为原逻辑。
    """
    skill_files = [p for p in (skill_dir / "SKILL.md", skill_dir / "SKILL.local.md") if p.exists()]
    if not skill_files or not log_path.exists():
        return False
    latest_issue = datetime.min
    for line in log_path.read_text(encoding="utf-8").splitlines():
        m = _LOG_LINE_RE.match(line)
        if m and m.group("result") in ("失败", "改进"):
            try:
                d = datetime.strptime(m.group("date"), "%Y-%m-%d")
            except ValueError:
                continue
            if d > latest_issue:
                latest_issue = d
    if latest_issue == datetime.min:
        return False
    return max(p.stat().st_mtime for p in skill_files) > latest_issue.timestamp()


def audit_skill(skill_name: str) -> SkillAudit:
    """评估技能健康度：成功率 + 未处理改进建议 → 是否需要修订。"""
    d = _skill_dir(skill_name)
    audit = SkillAudit(skill=skill_name)
    path = d / ".memory" / "experience.log"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            m = _LOG_LINE_RE.match(line)
            if not m:
                continue
            result = m.group("result")
            audit.results[result] += 1
            audit.total += 1
            if result in ("失败", "改进") and m.group("lesson").strip():
                audit.lessons.append(f"{result}: {m.group('lesson').strip()}")
    audit.improvements = _read_improvements(skill_name)
    if audit.total > 0:
        audit.success_rate = audit.results.get("成功", 0) / audit.total
    published = _revision_published_since_last_issue(d, path)
    audit.needs_revision = (
        audit.total > 0
        and not published
        and (
            audit.success_rate < SUCCESS_RATE_THRESHOLD
            or len(audit.improvements) >= IMPROVEMENTS_THRESHOLD
        )
    )
    audit.revision_published = published
    return audit


def print_audit(audit: SkillAudit) -> None:
    """打印审计报告。"""
    print(f"技能: {audit.skill}")
    print(f"  评估: {audit.summary}")
    if audit.revision_published:
        print("  健康度: ✓ 已发布修订版，等待新样本（不因历史低成功率重复报修订）")
    else:
        print(f"  健康度: {'⚠ 建议修订（生成改进版本）' if audit.needs_revision else '✓ 运行健康'}")
    if audit.lessons:
        print("  经验教训:")
        for lesson in audit.lessons[:10]:
            print(f"    - {lesson}")
    if audit.improvements:
        print("  未处理改进建议:")
        for imp in audit.improvements[:10]:
            print(f"    - {imp}")
    if audit.needs_revision:
        print("\n  发布建议: 按 skills/evoskills 技能流程生成改进版本 → 验证 → 更新 SKILL.md")
