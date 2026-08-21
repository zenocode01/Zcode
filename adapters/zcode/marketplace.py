"""技能市场与质量评估（Phase 4 生态）。

功能:
- build_marketplace(): 扫描 skills/ 生成市场清单 marketplace.json
- validate_skill(): 技能质量校验（frontmatter/命名/双版本/体积/占位符）
- generate_claude_plugin(): 生成 Claude Code 插件（.claude-plugin/marketplace.json + plugin.json）
- generate_opencode_config(): 输出 opencode.json 权限配置建议
- generate_kimi_plugin(): 生成 Kimi Code 插件注册（plugins/installed.json）
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import __version__

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"
MARKETPLACE_FILE = REPO_ROOT / "marketplace.json"
PLUGIN_DIR = REPO_ROOT / ".claude-plugin"

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# 占位符：仅匹配大写 TBD/TODO（小写 todo=任务清单不算）；"implement later"/"待补充"按字面
PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|implement later|待补充)\b")
# 否定语境：规则示例（"禁止 TBD/TODO""无占位符"）不算占位符
NEGATION_RE = re.compile(r"禁止|不要|不允|无|avoid|without", re.IGNORECASE)

# 本地精简版体积上限（字符；≈3K tokens）
LOCAL_MAX_CHARS = 12000


def _skill_names() -> list[str]:
    if not SKILLS_DIR.exists():
        return []
    return sorted(d.name for d in SKILLS_DIR.iterdir() if d.is_dir() and not d.name.startswith("_"))


def _read_frontmatter(text: str) -> dict:
    """提取 YAML frontmatter 的关键字段（name/description）。"""
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fields = {}
    for line in m.group(1).splitlines():
        km = re.match(r"^(\w+):\s*(.+)$", line.strip())
        if km:
            fields[km.group(1)] = km.group(2).strip()
    return fields


def validate_skill(name: str) -> list[str]:
    """校验技能质量，返回问题列表（空 = 通过）。"""
    issues: list[str] = []
    d = SKILLS_DIR / name
    if not d.is_dir():
        return [f"技能目录不存在: {name}"]

    if not NAME_RE.match(name):
        issues.append(f"命名违反约束 ^[a-z0-9]+(-[a-z0-9]+)*$: {name}")

    for variant, fname in (("标准", "SKILL.md"), ("本地", "SKILL.local.md")):
        f = d / fname
        if not f.exists():
            issues.append(f"缺 {variant}版: {fname}")
            continue
        text = f.read_text(encoding="utf-8")
        fm = _read_frontmatter(text)
        if "name" not in fm:
            issues.append(f"{fname}: 缺 frontmatter name")
        if "description" not in fm:
            issues.append(f"{fname}: 缺 frontmatter description")
        if fm.get("name") != name:
            issues.append(f"{fname}: frontmatter name({fm.get('name')}) 与目录名不一致")
        if any(PLACEHOLDER_RE.search(ln) and not NEGATION_RE.search(ln) for ln in text.splitlines()):
            issues.append(f"{fname}: 含占位符(TBD/TODO/implement later/待补充)")
        if fname == "SKILL.local.md" and len(text) > LOCAL_MAX_CHARS:
            issues.append(f"本地版超体积上限({LOCAL_MAX_CHARS}字符, 实际{len(text)})")

    return issues


def validate_all() -> dict[str, list[str]]:
    """全量校验，返回 {技能名: [问题]}。"""
    return {name: validate_skill(name) for name in _skill_names()}


def build_marketplace() -> dict:
    """生成技能市场清单（扫描 skills/ + 质量状态）。"""
    names = _skill_names()
    skills = []
    for name in names:
        issues = validate_skill(name)
        f = SKILLS_DIR / name / "SKILL.md"
        desc = ""
        if f.exists():
            desc = _read_frontmatter(f.read_text(encoding="utf-8")).get("description", "")
        skills.append({
            "name": name,
            "description": desc,
            "valid": not issues,
            "issues": issues,
        })
    return {
        "name": "zcode-skills",
        "interface": {"displayName": "Zcode 技能库"},
        "version": __version__,
        "count": len(skills),
        "skills": skills,
    }


def write_marketplace() -> Path:
    """写入 marketplace.json 并返回路径。"""
    MARKETPLACE_FILE.write_text(
        json.dumps(build_marketplace(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return MARKETPLACE_FILE


# ---- 平台深度插件生成 ----

def generate_claude_plugin() -> Path:
    """生成 Claude Code 插件：.claude-plugin/marketplace.json + plugin.json。"""
    PLUGIN_DIR.mkdir(exist_ok=True)
    names = _skill_names()

    marketplace = {
        "name": "zcode-plugins",
        "interface": {"displayName": "Zcode 技能库"},
        "plugins": [{
            "name": "zcode",
            "source": {"source": "local", "path": str(REPO_ROOT)},
            "policy": {"installation": "AVAILABLE", "authentication": "OFF"},
            "category": "Productivity",
        }],
    }
    (PLUGIN_DIR / "marketplace.json").write_text(
        json.dumps(marketplace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    plugin = {
        "name": "zcode",
        "version": __version__,
        "description": "Zcode 技能库：" + "、".join(names),
        "skills": names,
    }
    (PLUGIN_DIR / "plugin.json").write_text(
        json.dumps(plugin, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return PLUGIN_DIR


def generate_opencode_config() -> dict:
    """返回 opencode.json 的 permission.skill 建议片段。"""
    return {
        "permission": {
            "skill": {
                "allow": _skill_names(),
            }
        }
    }


def generate_kimi_plugin() -> dict:
    """返回 Kimi Code plugins/installed.json 注册片段。"""
    return {
        "plugins": [{
            "name": "zcode-skills",
            "version": __version__,
            "description": "Zcode 技能库",
            "managed": True,
        }],
    }
