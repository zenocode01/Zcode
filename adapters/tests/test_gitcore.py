"""gitcore 基础封装测试。"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zcode import gitcore  # noqa: E402


def _git(root: Path, *args: str) -> int:
    return subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True).returncode


class GitCoreBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def make_repo(self) -> Path:
        repo = self.base / "repo"
        repo.mkdir()
        _git(repo, "init", "-q")
        return repo


class TestFindGitRoot(GitCoreBase):
    def test_finds_root_from_subdir(self):
        repo = self.make_repo()
        sub = repo / "a" / "b"
        sub.mkdir(parents=True)
        self.assertEqual(gitcore.find_git_root(sub), repo)

    def test_returns_none_outside_repo(self):
        self.make_repo()
        outside = self.base / "outside"
        outside.mkdir()
        self.assertIsNone(gitcore.find_git_root(outside))


class TestRunGit(GitCoreBase):
    def test_returns_code_and_output(self):
        repo = self.make_repo()
        code, out = gitcore.run_git(repo, ["rev-parse", "--is-inside-work-tree"])
        self.assertEqual(code, 0)
        self.assertEqual(out[0].strip(), "true")

    def test_error_merged_into_output(self):
        repo = self.make_repo()
        code, out = gitcore.run_git(repo, ["show", "nonexistent-ref"])
        self.assertNotEqual(code, 0)
        self.assertTrue(any("nonexistent-ref" in l for l in out))


class TestGitStatus(GitCoreBase):
    def test_empty_repo_state(self):
        repo = self.make_repo()
        state, files = gitcore.git_status(repo)
        self.assertIn(state.branch, ("master", "main"))
        self.assertEqual(state.ahead, 0)
        self.assertEqual(state.behind, 0)
        self.assertEqual(files, [])

    def test_untracked_and_staged(self):
        repo = self.make_repo()
        (repo / "a.txt").write_text("hello", encoding="utf-8")
        _git(repo, "add", "a.txt")
        state, files = gitcore.git_status(repo)
        by_path = {f.path: f for f in files}
        self.assertTrue(by_path["a.txt"].staged)
        self.assertFalse(by_path["a.txt"].untracked)

    def test_untracked_file(self):
        repo = self.make_repo()
        (repo / "u.txt").write_text("x", encoding="utf-8")
        state, files = gitcore.git_status(repo)
        by_path = {f.path: f for f in files}
        self.assertTrue(by_path["u.txt"].untracked)
        self.assertFalse(by_path["u.txt"].staged)

    def test_conflict_detection(self):
        repo = self.make_repo()
        (repo / "f.txt").write_text("base", encoding="utf-8")
        _git(repo, "add", "f.txt")
        _git(repo, "config", "user.email", "t@t")
        _git(repo, "config", "user.name", "t")
        _git(repo, "commit", "-q", "-m", "base")
        _git(repo, "checkout", "-q", "-b", "side")
        (repo / "f.txt").write_text("side", encoding="utf-8")
        _git(repo, "commit", "-qam", "side")
        _git(repo, "checkout", "-q", "master")
        (repo / "f.txt").write_text("master", encoding="utf-8")
        _git(repo, "commit", "-qam", "master")
        _git(repo, "merge", "side")  # 返回非 0，制造冲突
        state, files = gitcore.git_status(repo)
        self.assertTrue(any(f.conflicted for f in files))
        self.assertEqual(state.conflicts, ["f.txt"])


class TestGitLog(GitCoreBase):
    def _commit(self, repo: Path, msg: str):
        (repo / f"{msg}.txt").write_text(msg, encoding="utf-8")
        _git(repo, "add", ".")
        _git(repo, "config", "user.email", "t@t")
        _git(repo, "config", "user.name", "t")
        _git(repo, "commit", "-q", "-m", msg)

    def test_log_returns_commits(self):
        repo = self.make_repo()
        self._commit(repo, "first")
        self._commit(repo, "second")
        commits = gitcore.git_log(repo)
        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[0].subject, "second")  # 最新的在前
        self.assertEqual(commits[1].subject, "first")
        self.assertTrue(commits[0].hash)

    def test_log_limit(self):
        repo = self.make_repo()
        for i in range(5):
            self._commit(repo, f"c{i}")
        self.assertEqual(len(gitcore.git_log(repo, n=2)), 2)


class TestGitBranches(GitCoreBase):
    def test_branches_local_and_current(self):
        repo = self.make_repo()
        (repo / "f.txt").write_text("x", encoding="utf-8")
        _git(repo, "config", "user.email", "t@t")
        _git(repo, "config", "user.name", "t")
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "init")
        _git(repo, "branch", "feature")
        branches = gitcore.git_branches(repo)
        names = {b.name: b for b in branches}
        self.assertIn("feature", names)
        cur = [b for b in branches if b.is_current]
        self.assertEqual(len(cur), 1)


class TestGitStash(GitCoreBase):
    def test_stash_list(self):
        repo = self.make_repo()
        (repo / "f.txt").write_text("base", encoding="utf-8")
        _git(repo, "config", "user.email", "t@t")
        _git(repo, "config", "user.name", "t")
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "base")
        (repo / "f.txt").write_text("changed", encoding="utf-8")
        _git(repo, "stash", "push", "-q", "-m", "wip")
        entries = gitcore.git_stash_list(repo)
        self.assertEqual(len(entries), 1)
        self.assertIn("wip", entries[0].message)


class TestGitDiff(GitCoreBase):
    def test_diff_returns_text(self):
        repo = self.make_repo()
        (repo / "f.txt").write_text("base", encoding="utf-8")
        _git(repo, "config", "user.email", "t@t")
        _git(repo, "config", "user.name", "t")
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "base")
        (repo / "f.txt").write_text("changed", encoding="utf-8")
        text = gitcore.git_diff(repo)
        self.assertIn("changed", text)
        self.assertIn("-base", text)

    def test_diff_staged(self):
        repo = self.make_repo()
        (repo / "f.txt").write_text("base", encoding="utf-8")
        _git(repo, "config", "user.email", "t@t")
        _git(repo, "config", "user.name", "t")
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "base")
        (repo / "f.txt").write_text("changed", encoding="utf-8")
        _git(repo, "add", "f.txt")
        text = gitcore.git_diff(repo, staged=True)
        self.assertIn("changed", text)


class TestDangerous(GitCoreBase):
    def test_is_dangerous_reset_hard(self):
        self.assertTrue(gitcore.is_dangerous(["reset", "--hard", "HEAD~1"]))

    def test_is_dangerous_clean(self):
        self.assertTrue(gitcore.is_dangerous(["clean", "-f"]))

    def test_not_dangerous_status(self):
        self.assertFalse(gitcore.is_dangerous(["status"]))


class TestGitRun(GitCoreBase):
    def test_git_run_ok(self):
        repo = self.make_repo()
        code, out = gitcore.git_run(repo, ["rev-parse", "--git-dir"])
        self.assertEqual(code, 0)

    def test_git_run_raises_on_error(self):
        repo = self.make_repo()
        with self.assertRaises(gitcore.GitError):
            gitcore.git_run(repo, ["show", "no-such-ref"])


class TestGitWrite(GitCoreBase):
    def _init_commit(self, repo: Path):
        (repo / "f.txt").write_text("base", encoding="utf-8")
        _git(repo, "config", "user.email", "t@t")
        _git(repo, "config", "user.name", "t")
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "base")

    def test_git_add_and_commit(self):
        repo = self.make_repo()
        self._init_commit(repo)
        (repo / "g.txt").write_text("new", encoding="utf-8")
        code, _ = gitcore.git_add(repo, ["g.txt"])
        self.assertEqual(code, 0)
        _, files = gitcore.git_status(repo)
        self.assertTrue(any(f.path == "g.txt" and f.staged for f in files))
        code, _ = gitcore.git_commit(repo, "add g")
        self.assertEqual(code, 0)
        commits = gitcore.git_log(repo)
        self.assertEqual(commits[0].subject, "add g")

    def test_git_checkout(self):
        repo = self.make_repo()
        self._init_commit(repo)
        _git(repo, "branch", "feature")
        code, _ = gitcore.git_checkout(repo, "feature")
        self.assertEqual(code, 0)
        _, out = gitcore.run_git(repo, ["branch", "--show-current"])
        self.assertEqual(out[0].strip(), "feature")
