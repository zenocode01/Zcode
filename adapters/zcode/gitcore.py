"""git 仓库封装：执行 + 结构化解析（零第三方依赖）。

设计：逻辑层，供 gittui（视图）/ gitcli（非 TTY 命令）共用。
所有写操作委托 git CLI（`git -C <root> ...`），zcode 不重实现 git 语义。
"""
from __future__ import annotations

import subprocess
import re
from dataclasses import dataclass, field
from pathlib import Path


class GitError(Exception):
    """git 操作失败（携带退出码与输出，便于视图层分类提示）。"""

    def __init__(self, message: str, code: int = 1, output: list[str] | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.output = output or []

    def __str__(self) -> str:
        detail = (" — " + "\n".join(self.output[-3:])) if self.output else ""
        return f"{self.message}{detail}"


@dataclass
class FileStatus:
    """单个文件的工作区/暂存区状态。"""
    path: str
    index: str = "."          # X 状态码（index 侧）
    worktree: str = "."       # Y 状态码（worktree 侧）
    staged: bool = False
    untracked: bool = False
    conflicted: bool = False


@dataclass
class RepoState:
    """仓库整体状态（分支/上游/领先落后/冲突文件）。"""
    branch: str = ""
    upstream: str | None = None
    ahead: int = 0
    behind: int = 0
    conflicts: list[str] = field(default_factory=list)


@dataclass
class CommitInfo:
    """一条提交记录。"""
    hash: str = ""
    parents: list[str] = field(default_factory=list)
    author: str = ""
    date: str = ""
    subject: str = ""
    refs: str = ""


@dataclass
class BranchInfo:
    """一个分支。"""
    name: str = ""
    is_local: bool = True
    is_current: bool = False
    upstream: str | None = None


@dataclass
class StashEntry:
    """一条 stash。"""
    ref: str = ""
    message: str = ""


def find_git_root(start: Path | None = None) -> Path | None:
    """沿父目录向上找 .git（文件或目录都算），找不到返回 None。"""
    p = (start or Path.cwd()).resolve()
    while True:
        if (p / ".git").exists():
            return p
        if p.parent == p:
            return None
        p = p.parent


def run_git(root: Path, args: list[str]) -> tuple[int, list[str]]:
    """执行 `git -C root args`，stdout+stderr 合并分行返回 (退出码, 行列表)。"""
    r = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, errors="replace",
    )
    out = (r.stdout or "").splitlines()
    if r.returncode != 0 and r.stderr:
        out.extend((r.stderr or "").splitlines())
    return r.returncode, out


def git_status(root: Path) -> tuple[RepoState, list[FileStatus]]:
    """解析 `git status --porcelain=v2 --branch`，返回仓库状态与文件列表。

    porcelain v2 条目格式：
      `# branch.head <name>` / `# branch.upstream <up>` / `# branch.ab +<a> -<b>`
      `1 <XY> <sub> ... <path>`（普通）/ `2 <XY> ... <path>`（改名）
      `u <XY> ... <path>`（未合并冲突）/ `? <path>`（未跟踪）
    """
    code, out = run_git(root, ["status", "--porcelain=v2", "--branch"])
    if code != 0:
        raise GitError("git status 失败", code, out)

    state = RepoState()
    files: list[FileStatus] = []
    for line in out:
        if line.startswith("# branch.head "):
            state.branch = line[len("# branch.head "):].strip()
        elif line.startswith("# branch.upstream "):
            state.upstream = line[len("# branch.upstream "):].strip()
        elif line.startswith("# branch.ab "):
            # 形如 "+1 -0"
            ab = line[len("# branch.ab "):].strip()
            for tok in ab.split():
                if tok.startswith("+"):
                    state.ahead = int(tok[1:])
                elif tok.startswith("-"):
                    state.behind = int(tok[1:])
        elif line.startswith("? "):
            files.append(FileStatus(
                path=line[2:], worktree="?", untracked=True,
            ))
        elif line.startswith("u "):
            parts = line.split(maxsplit=10)
            xy = parts[1] if len(parts) > 1 else ".."
            path = parts[10] if len(parts) > 10 else ""
            fs = FileStatus(path=path, index=xy[0], worktree=xy[1], conflicted=True)
            files.append(fs)
            if path:
                state.conflicts.append(path)
        elif line.startswith("1 ") or line.startswith("2 "):
            parts = line.split(maxsplit=8)
            xy = parts[1] if len(parts) > 1 else ".."
            path = parts[8] if len(parts) > 8 else ""
            x, y = (xy[0], xy[1]) if len(xy) >= 2 else (".", ".")
            files.append(FileStatus(
                path=path,
                index=x,
                worktree=y,
                staged=(x != "."),
                conflicted=(x == "U" or y == "U"),
            ))
            if x == "U" or y == "U":
                if path and path not in state.conflicts:
                    state.conflicts.append(path)
    return state, files


def git_log(root: Path, n: int = 50) -> list[CommitInfo]:
    """解析提交历史（最新在前）。无提交（空仓库）返回空列表。"""
    # 无 HEAD = 尚无提交
    code, _ = run_git(root, ["rev-parse", "--verify", "HEAD"])
    if code != 0:
        return []
    code, out = run_git(
        root,
        ["log", f"-{n}", "--format=%H%x00%P%x00%an%x00%ad%x00%s%x00%D"],
    )
    if code != 0:
        raise GitError("git log 失败", code, out)
    commits: list[CommitInfo] = []
    for line in out:
        parts = line.split("\x00")
        if len(parts) < 6:
            continue
        commits.append(CommitInfo(
            hash=parts[0].strip(),
            parents=[p for p in parts[1].split() if p],
            author=parts[2].strip(),
            date=parts[3].strip(),
            subject=parts[4].strip(),
            refs=parts[5].strip(),
        ))
    return commits


def git_branches(root: Path) -> list[BranchInfo]:
    """解析本地 + 远程分支；`*` 前缀为当前分支。"""
    code, out = run_git(root, ["branch", "-vv", "--no-color"])
    if code != 0:
        raise GitError("git branch 失败", code, out)
    branches: list[BranchInfo] = []
    for line in out:
        if not line.strip():
            continue
        is_current = line.startswith("*")
        body = line[1:].strip() if is_current else line.strip()
        # 形如 "feature  abc1234 [origin/feature] 提交说明"
        tokens = body.split(None, 2)
        name = tokens[0] if tokens else ""
        upstream: str | None = None
        if len(tokens) >= 2:
            m = re.search(r"\[([^\]]+)\]", tokens[1])
            if m:
                upstream = m.group(1).split(":")[0]
        branches.append(BranchInfo(
            name=name, is_local=True, is_current=is_current, upstream=upstream,
        ))
    # 远程分支
    code2, out2 = run_git(root, ["branch", "-r", "--no-color"])
    if code2 == 0:
        for line in out2:
            name = line.strip().lstrip("*").strip()
            if not name or name.startswith("HEAD ->"):
                continue
            branches.append(BranchInfo(name=name, is_local=False))
    return branches


def git_stash_list(root: Path) -> list[StashEntry]:
    """解析 stash 列表。"""
    code, out = run_git(root, ["stash", "list"])
    if code != 0:
        raise GitError("git stash list 失败", code, out)
    entries: list[StashEntry] = []
    for line in out:
        # 形如 "stash@{0}: On master: wip"
        if ":" not in line:
            continue
        ref, rest = line.split(":", 1)
        entries.append(StashEntry(ref=ref.strip(), message=rest.strip()))
    return entries


def git_diff(root: Path, target: str | None = None, staged: bool = False) -> str:
    """返回 diff 文本；staged=True 时看暂存区（--cached）。"""
    args = ["diff"]
    if staged:
        args.append("--cached")
    if target:
        args += ["--", target]
    code, out = run_git(root, args)
    if code != 0:
        raise GitError("git diff 失败", code, out)
    return "\n".join(out)


# 危险命令：执行前需二次确认/警告（视图层据此拦截或提示）
DANGEROUS = (
    ("reset", "--hard"),
    ("clean", "-f"),
    ("push", "--force"),
    ("push", "-f"),
    ("checkout", "--"),
)


def is_dangerous(args: list[str]) -> bool:
    """判断参数序列是否命中危险模式。"""
    for i, a in enumerate(args):
        for pat in DANGEROUS:
            if args[i:i + len(pat)] == list(pat):
                return True
    return False


def git_run(root: Path, args: list[str]) -> tuple[int, list[str]]:
    """执行 git；失败抛 GitError（成功返回 (code, out)）。"""
    code, out = run_git(root, args)
    if code != 0:
        raise GitError(f"git {' '.join(args)} 失败", code, out)
    return code, out


def git_add(root: Path, paths: list[str]) -> tuple[int, list[str]]:
    return git_run(root, ["add", "--", *paths])


def git_commit(root: Path, message: str) -> tuple[int, list[str]]:
    return git_run(root, ["commit", "-m", message])


def git_push(root: Path, remote: str = "origin", branch: str | None = None) -> tuple[int, list[str]]:
    args = ["push", remote]
    if branch:
        args.append(branch)
    return git_run(root, args)


def git_pull(root: Path, remote: str = "origin", branch: str | None = None) -> tuple[int, list[str]]:
    args = ["pull", remote]
    if branch:
        args.append(branch)
    return git_run(root, args)


def git_fetch(root: Path, remote: str = "origin") -> tuple[int, list[str]]:
    return git_run(root, ["fetch", remote])


def git_checkout(root: Path, ref: str) -> tuple[int, list[str]]:
    return git_run(root, ["checkout", ref])


def git_merge(root: Path, ref: str) -> tuple[int, list[str]]:
    return git_run(root, ["merge", ref])


def git_stash(root: Path, action: str, extra: list[str] | None = None) -> tuple[int, list[str]]:
    return git_run(root, ["stash", action, *(extra or [])])


def git_rebase(root: Path, ref: str) -> tuple[int, list[str]]:
    return git_run(root, ["rebase", ref])


def git_cherry_pick(root: Path, ref: str) -> tuple[int, list[str]]:
    return git_run(root, ["cherry-pick", ref])


def git_tag(root: Path, action: str, name: str, extra: list[str] | None = None) -> tuple[int, list[str]]:
    return git_run(root, ["tag", action, name, *(extra or [])])


def git_remote(root: Path, action: str, extra: list[str] | None = None) -> tuple[int, list[str]]:
    return git_run(root, ["remote", action, *(extra or [])])


def git_reset(root: Path, mode: str, ref: str) -> tuple[int, list[str]]:
    return git_run(root, ["reset", mode, ref])


def git_revert(root: Path, ref: str) -> tuple[int, list[str]]:
    return git_run(root, ["revert", "--no-edit", ref])
