"""gitcli 非 TTY 逐条命令测试。"""
from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zcode import gitcli, gitcore  # noqa: E402


def _git(root: Path, *args: str) -> int:
    return subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True).returncode


class GitCliBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        _git(self.repo, "init", "-q")
        self.old_cwd = os.getcwd()
        os.chdir(self.repo)
        self.addCleanup(self._restore)

    def _restore(self):
        os.chdir(self.old_cwd)
        self._tmp.cleanup()

    def _commit(self, msg: str):
        (self.repo / f"{msg}.txt").write_text(msg, encoding="utf-8")
        _git(self.repo, "config", "user.email", "t@t")
        _git(self.repo, "config", "user.name", "t")
        _git(self.repo, "add", ".")
        _git(self.repo, "commit", "-q", "-m", msg)

    def _run(self, *argv: str) -> str:
        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            gitcli.run(list(argv))
        return buf.getvalue()


class TestStatus(GitCliBase):
    def test_status_no_color_and_untracked(self):
        (self.repo / "u.txt").write_text("x", encoding="utf-8")
        out = self._run("status")
        self.assertIn("未跟踪", out)
        self.assertIn("u.txt", out)
        self.assertNotIn("\033", out)  # 非 TTY 无 ANSI

    def test_status_group_staged(self):
        (self.repo / "s.txt").write_text("x", encoding="utf-8")
        _git(self.repo, "add", "s.txt")
        out = self._run("status")
        self.assertIn("已暂存", out)
        self.assertIn("s.txt", out)


class TestLog(GitCliBase):
    def test_log_shows_subject(self):
        self._commit("hello-subject")
        out = self._run("log")
        self.assertIn("hello-subject", out)


class TestDiff(GitCliBase):
    def test_diff_shows_change(self):
        self._commit("base")
        (self.repo / "base.txt").write_text("changed", encoding="utf-8")
        out = self._run("diff")
        self.assertIn("changed", out)


class TestNotInRepo(GitCliBase):
    def test_status_outside_repo(self):
        os.chdir(self.base)  # 非仓库目录
        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            rc = gitcli.run(["status"])
        self.assertEqual(rc, 1)


class TestDangerous(GitCliBase):
    def test_reset_hard_warns(self):
        with mock.patch.object(gitcore, "git_reset", return_value=(0, [])):
            out = self._run("reset", "--hard", "HEAD")
        self.assertIn("危险", out)
