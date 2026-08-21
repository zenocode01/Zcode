"""gitcli — zcode git 的非 TTY 逐条命令 + 彩色渲染。

TTY 下进全屏 TUI（gittui）；非 TTY（CI/管道/脚本）退化为逐条彩色输出，
复用同一逻辑层 gitcore。彩色仅当 stdout 为 TTY 时启用。
"""
from __future__ import annotations

import sys

from . import gitcore

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _tty() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _color(code: str, text: str) -> str:
    return f"{code}{text}{RESET}" if _tty() else text


def _root() -> tuple[gitcore.Path | None, int]:
    """定位仓库根；不在仓库返回 (None, 1)。"""
    root = gitcore.find_git_root()
    if root is None:
        print("错误: 当前目录不在 git 仓库内", file=sys.stderr)
        return None, 1
    return root, 0


def _status(root) -> int:
    state, files = gitcore.git_status(root)
    print(_color(BOLD, f"分支 {state.branch}") +
          (f"  上游 {state.upstream}" if state.upstream else "") +
          (f"  ↑{state.ahead} ↓{state.behind}" if state.ahead or state.behind else ""))
    if state.conflicts:
        print(_color(RED, f"冲突: {len(state.conflicts)} 个文件") + " " + ", ".join(state.conflicts))
    staged = [f for f in files if f.staged and not f.conflicted]
    unstaged = [f for f in files if not f.staged and not f.untracked and not f.conflicted]
    untracked = [f for f in files if f.untracked]
    conflicted = [f for f in files if f.conflicted]

    def _section(title: str, items, color: str) -> None:
        if not items:
            return
        print(_color(color, title))
        for f in items:
            mark = f.index + f.worktree if f.index != "." or f.worktree != "." else "  "
            print(f"  {mark} {f.path}")

    _section("已暂存", staged, GREEN)
    _section("未暂存", unstaged, YELLOW)
    _section("未跟踪", untracked, CYAN)
    _section("冲突", conflicted, RED)
    return 0


def _log(root) -> int:
    commits = gitcore.git_log(root)
    if not commits:
        print("(尚无提交)")
        return 0
    for c in commits:
        refs = f" {_color(CYAN, c.refs)}" if c.refs else ""
        print(f"{_color(YELLOW, c.hash[:7])} {c.subject}{refs}")
        print(f"  {c.author}  {c.date}")
    return 0


def _diff(root, args) -> int:
    staged = "--staged" in args or "--cached" in args
    targets = [a for a in args if not a.startswith("--")]
    text = gitcore.git_diff(root, target=targets[0] if targets else None, staged=staged)
    print(text if text else "(无差异)")
    return 0


def _warn_danger(args: list[str]) -> None:
    if gitcore.is_dangerous(args):
        print(_color(RED, f"⚠ 危险操作: git {' '.join(args)}"))


def run(argv: list[str]) -> int:
    """分发 zcode git <子命令> [args...]。返回退出码。"""
    if not argv:
        print("用法: zcode git <status|log|diff|add|commit|push|pull|fetch|branch|checkout|merge|stash|rebase|cherry-pick|tag|remote|reset|revert> [args]")
        return 0
    cmd = argv[0]
    args = argv[1:]

    # 只读命令：不需要仓库也能给帮助，但实际执行需仓库
    root, rc = _root()
    if root is None:
        return rc

    try:
        if cmd == "status":
            return _status(root)
        if cmd == "log":
            return _log(root)
        if cmd == "diff":
            return _diff(root, args)
        if cmd == "add":
            _warn_danger(argv)
            code, out = gitcore.git_add(root, args if args else ["."])
            return _finish(code, out)
        if cmd == "commit":
            msg = ""
            if "-m" in args:
                i = args.index("-m")
                msg = args[i + 1] if i + 1 < len(args) else ""
            code, out = gitcore.git_commit(root, msg)
            return _finish(code, out)
        if cmd in ("push", "pull", "fetch"):
            _warn_danger(argv)
            remote = args[0] if args else "origin"
            branch = args[1] if len(args) > 1 else None
            fn = {"push": gitcore.git_push, "pull": gitcore.git_pull, "fetch": gitcore.git_fetch}[cmd]
            code, out = fn(root, remote, branch) if cmd != "fetch" else fn(root, remote)
            return _finish(code, out)
        if cmd == "branch":
            if args and args[0] not in ("-a", "--all"):
                code, out = gitcore.git_run(root, ["branch", *args])
                return _finish(code, out)
            for b in gitcore.git_branches(root):
                mark = "*" if b.is_current else " "
                print(f"{mark} {_color(GREEN if b.is_current else '', b.name)}")
            return 0
        if cmd == "checkout":
            code, out = gitcore.git_checkout(root, args[0] if args else "")
            return _finish(code, out)
        if cmd == "merge":
            code, out = gitcore.git_merge(root, args[0] if args else "")
            return _finish(code, out)
        if cmd == "stash":
            action = args[0] if args else "list"
            if action == "list":
                for e in gitcore.git_stash_list(root):
                    print(f"{e.ref}: {e.message}")
                return 0
            code, out = gitcore.git_stash(root, action)
            return _finish(code, out)
        if cmd == "rebase":
            code, out = gitcore.git_rebase(root, args[0] if args else "")
            return _finish(code, out)
        if cmd == "cherry-pick":
            code, out = gitcore.git_cherry_pick(root, args[0] if args else "")
            return _finish(code, out)
        if cmd == "tag":
            action = args[0] if args else "list"
            if action == "list":
                code, out = gitcore.run_git(root, ["tag", "--list"])
                for line in out:
                    print(line)
                return 0 if code == 0 else 1
            code, out = gitcore.git_tag(root, action, args[1] if len(args) > 1 else "")
            return _finish(code, out)
        if cmd == "remote":
            action = args[0] if args else "list"
            if action in ("list", "-v"):
                code, out = gitcore.run_git(root, ["remote", "-v"])
                for line in out:
                    print(line)
                return 0 if code == 0 else 1
            code, out = gitcore.git_remote(root, action, args[1:])
            return _finish(code, out)
        if cmd == "reset":
            _warn_danger(argv)
            mode = args[0] if args else "--mixed"
            ref = args[1] if len(args) > 1 else "HEAD"
            code, out = gitcore.git_reset(root, mode, ref)
            return _finish(code, out)
        if cmd == "revert":
            code, out = gitcore.git_revert(root, args[0] if args else "")
            return _finish(code, out)
        print(f"未知子命令: {cmd}", file=sys.stderr)
        return 1
    except gitcore.GitError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


def _finish(code: int, out: list[str]) -> int:
    if code == 0:
        for line in out[-5:]:
            print(line)
        return 0
    print("操作失败:", file=sys.stderr)
    for line in out[-10:]:
        print(f"  {line}", file=sys.stderr)
    return 1
