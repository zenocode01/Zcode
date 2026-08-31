"""EvoSkills 审计闭环测试（unittest，零依赖）。

背景：audit_skill 的 needs_revision 只由历史成功率判定。改进版本发布后
成功率不变，导致"发布后重审计确认健康度回升"无法闭环。
本测试锁定修复后的期望行为：技能文件在最近失败/改进记录之后被修改过
（即已发布修订版），不再仅因历史成功率建议修订，而是等待新样本。
"""
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zcode import evoskills  # noqa: E402


def _make_skill(tmp: Path, log_lines: list[str], skill_mtime: datetime | None) -> Path:
    """建一个虚拟技能目录：experience.log + SKILL.md（可选 mtime）。"""
    d = tmp / "fake-skill"
    mem = d / ".memory"
    mem.mkdir(parents=True)
    (mem / "experience.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    if skill_mtime is not None:
        skill = d / "SKILL.md"
        skill.write_text("# fake\n", encoding="utf-8")
        os.utime(skill, (skill_mtime.timestamp(), skill_mtime.timestamp()))
    return d


class AuditClosedLoopTest(unittest.TestCase):
    """发布修订版后，audit 不应再仅因历史低成功率建议修订。"""

    LOG_60PCT = [
        "2026-08-01 | 功能开发 | 成功 | 先写失败测试再实现",
        "2026-08-02 | 功能开发 | 成功 | 先写失败测试再实现",
        "2026-08-03 | 功能开发 | 成功 | 先写失败测试再实现",
        "2026-08-04 | 紧急修复 | 失败 | 跳过测试直接改，引入了回归",
        "2026-08-05 | 性能优化 | 失败 | 没有先建反馈回路就动手",
    ]

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patcher = patch.object(evoskills, "SKILLS_DIR", Path(self.tmp.name))
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.tmp.cleanup()

    def test_published_revision_is_healthy(self):
        """技能文件修改时间晚于最近失败 → 已发布修订版，不再建议修订。"""
        published = datetime(2026, 8, 6, 10, 0)  # 晚于 08-05 的失败
        _make_skill(Path(self.tmp.name), self.LOG_60PCT, published)
        audit = evoskills.audit_skill("fake-skill")
        self.assertEqual(audit.success_rate, 0.6)
        self.assertFalse(audit.needs_revision, "已发布修订版不应仍建议修订")

    def test_unpublished_revision_still_needs_revision(self):
        """技能文件未在失败后被修改 → 仍应建议修订。"""
        old = datetime(2026, 8, 4, 10, 0)  # 早于 08-05 的失败
        _make_skill(Path(self.tmp.name), self.LOG_60PCT, old)
        audit = evoskills.audit_skill("fake-skill")
        self.assertTrue(audit.needs_revision, "未发布修订版应继续建议修订")

    def test_no_skill_file_uses_fallback_revision(self):
        """无技能文件时退化为原逻辑：低成功率仍建议修订。"""
        _make_skill(Path(self.tmp.name), self.LOG_60PCT, None)
        audit = evoskills.audit_skill("fake-skill")
        self.assertTrue(audit.needs_revision)

    def test_no_log_is_healthy(self):
        """无使用记录 → 样本不足，不强制迭代。"""
        (Path(self.tmp.name) / "fake-skill").mkdir(parents=True)
        audit = evoskills.audit_skill("fake-skill")
        self.assertFalse(audit.needs_revision)


if __name__ == "__main__":
    unittest.main()
