"""release.py（版本迭代命令）单元测试。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zcode import release  # noqa: E402


class TestBumpVersion(unittest.TestCase):
    def test_patch(self):
        self.assertEqual(release.bump_version("0.3.8", "patch"), "0.3.9")

    def test_minor(self):
        self.assertEqual(release.bump_version("0.3.8", "minor"), "0.4.0")

    def test_major(self):
        self.assertEqual(release.bump_version("0.3.8", "major"), "1.0.0")

    def test_manual(self):
        self.assertEqual(release.bump_version("0.3.8", "0.5.0"), "0.5.0")

    def test_manual_not_greater_rejected(self):
        with self.assertRaises(release.ReleaseError):
            release.bump_version("0.3.8", "0.3.8")

    def test_invalid_rejected(self):
        with self.assertRaises(release.ReleaseError):
            release.bump_version("0.3.8", "foo")


class TestCollectUnreleased(unittest.TestCase):
    CONTENT = (
        "# Changelog\n\n"
        "## [未发布]\n\n"
        "**工单A**（T-001）：aaa\n\n"
        "## [0.3.9] - 2026-08-01\n\n"
        "**旧变更**（T-000）：bbb\n\n"
        "## [0.3.8] - 2026-07-01\n\n"
        "**历史**：ccc\n"
    )

    def test_collect_unreleased_and_newer(self):
        got = release.collect_unreleased(self.CONTENT, "0.3.8")
        self.assertIn("工单A", got)
        self.assertIn("旧变更", got)
        self.assertNotIn("历史", got)  # <= current 的不收集

    def test_collect_empty(self):
        got = release.collect_unreleased("## [0.3.8]\n\n历史\n", "0.3.8")
        self.assertEqual(got, "")


class TestRebuildChangelog(unittest.TestCase):
    CONTENT = (
        "# Changelog\n\n"
        "## [未发布]\n\n"
        "**工单A**（T-001）：aaa\n\n"
        "## [0.3.9] - 2026-08-01\n\n"
        "**旧变更**：bbb\n\n"
        "## [0.3.8] - 2026-07-01\n\n"
        "**历史**：ccc\n"
    )

    def test_rebuild_merges_and_keeps_history(self):
        got = release.rebuild_changelog(self.CONTENT, "0.4.0", "0.3.8")
        self.assertIn("## [0.4.0]", got)
        self.assertIn("工单A", got)      # 未发布归并
        self.assertIn("旧变更", got)     # > current 归并
        self.assertIn("## [0.3.8]", got)  # 历史保留
        self.assertIn("历史", got)
        self.assertNotIn("[未发布]", got)  # 未发布区块已移除
        self.assertNotIn("[0.3.9]", got)   # 旧版本号区块已移除

    def test_rebuild_no_unreleased(self):
        content = "# Changelog\n\n## [0.3.8] - 2026-07-01\n\n**历史**：ccc\n"
        got = release.rebuild_changelog(content, "0.3.9", "0.3.8")
        self.assertIn("## [0.3.9]", got)
        self.assertIn("（无变更记录）", got)
        self.assertIn("## [0.3.8]", got)


class TestWriteVersionFiles(unittest.TestCase):
    def test_write_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            files = [
                (base / "a.py", '__version__ = "[^"]+"', '__version__ = "{}"'),
                (base / "b.json", '"version": "[^"]+"', '"version": "{}"'),
            ]
            (base / "a.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")
            (base / "b.json").write_text('{"version": "0.1.0"}\n', encoding="utf-8")
            with mock.patch.object(release, "VERSION_FILES", files):
                changed = release.write_version_files("0.2.0")
            self.assertEqual(len(changed), 2)
            self.assertIn('__version__ = "0.2.0"', (base / "a.py").read_text(encoding="utf-8"))
            self.assertIn('"version": "0.2.0"', (base / "b.json").read_text(encoding="utf-8"))


class TestRunReleaseDryRun(unittest.TestCase):
    def test_dry_run_no_side_effect(self):
        with mock.patch.object(release, "current_version", return_value="0.3.8"):
            rc = release.run_release("minor", dry_run=True)
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
