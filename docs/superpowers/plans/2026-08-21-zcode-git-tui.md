# 实现计划 — zcode git 交互式 TUI 仓库管理（T-026）

- 日期：2026-08-21
- 关联 spec：`docs/superpowers/specs/2026-08-21-zcode-git-tui-design.md`
- 关联工单：T-026

## Goal

新增 `zcode git` 子命令族：零依赖逻辑层 `gitcore.py` + 非 TTY 逐条命令 `gitcli.py` + textual 全屏 TUI `gittui.py`，覆盖核心日常与进阶 git 操作。

## Architecture

```
adapters/zcode/gitcore.py   # 纯逻辑：git 执行封装 + 结构化解析（零第三方依赖）
adapters/zcode/gitcli.py    # 非 TTY：子命令分发 + 彩色渲染（复用 gitcore）
adapters/zcode/gittui.py    # textual App：多面板 + 键盘绑定（仅此文件 import textual）
adapters/zcode/cli.py       # 注册 zcode git 入口（TTY→gittui，非 TTY→gitcli）
adapters/tests/test_gitcore.py
adapters/tests/test_gitcli.py
```

依赖方向：`cli.py → gittui.py / gitcli.py → gitcore.py`。gitcore 不 import 任何 zcode 其他模块、不 import textual。

## Tech Stack

- Python ≥3.10（仓库现有 3.14.4），`subprocess` 委托 git CLI
- TUI：`textual`（仅 gittui.py 依赖；安装 `pip install textual`，不 pin 版本，若 Python 3.14 解析失败则按 spec 第 10 节回退 urwid，分层不变）
- 测试：`unittest` + `tempfile.TemporaryDirectory` 临时仓库夹具（沿用 test_ticket 模式）

## Global Constraints

1. gitcore.py 零第三方依赖；textual 只允许出现在 gittui.py。
2. 所有写操作委托 git CLI（`git -C <root> ...`），zcode 不重实现 git 语义。
3. 危险命令（`reset --hard`、`clean -f`、`push --force`、`checkout -- <file>` 丢弃工作区）必须二次确认或打印警告。
4. 非 TTY（`sys.stdout.isatty()` 为 False）时 `zcode git` 必须退化为逐条命令，绝不尝试启动 textual。
5. 中文输出（项目文档语言约定）；代码注释中文。
6. 每任务以「写失败测试 → 跑确认失败 → 最小实现 → 跑确认通过 → commit」结尾。
7. 测试门禁命令：`.venv/bin/python -m unittest discover -s adapters/tests`（现有 84 用例 + 新增全绿）。

---

## Task 1 — gitcore 基础：仓库定位 + 执行封装 + GitError

**Files**
- Create `adapters/zcode/gitcore.py`
- Create `adapters/tests/test_gitcore.py`

**Interfaces**
- Consumes: 无（仅标准库）
- Produces:
  - `class GitError(Exception)` — `message: str`、`code: int`、`output: list[str]`
  - `def find_git_root(start: Path | None = None) -> Path | None` — 沿父目录找 `.git`（文件或目录都算）
  - `def run_git(root: Path, args: list[str]) -> tuple[int, list[str]]` — 执行 `git -C root args`，stdout+stderr 合并分行返回

**步骤**

- [ ] 写失败测试 `test_gitcore.py`：

```python
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
        _git(self.base, "init", "-q")
        return self.base


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
```

- [ ] 跑确认失败：`ModuleNotFoundError: No module named 'zcode.gitcore'`
- [ ] 最小实现 `gitcore.py`：

```python
"""git 仓库封装：执行 + 结构化解析（零第三方依赖）。"""
from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(Exception):
    def __init__(self, message: str, code: int = 1, output: list[str] | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.output = output or []

    def __str__(self) -> str:
        detail = (" — " + "\n".join(self.output[-3:])) if self.output else ""
        return f"{self.message}{detail}"


def find_git_root(start: Path | None = None) -> Path | None:
    p = (start or Path.cwd()).resolve()
    while True:
        if (p / ".git").exists():
            return p
        if p.parent == p:
            return None
        p = p.parent


def run_git(root: Path, args: list[str]) -> tuple[int, list[str]]:
    r = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, errors="replace",
    )
    out = (r.stdout or "").splitlines()
    if r.returncode != 0 and r.stderr:
        out.extend((r.stderr or "").splitlines())
    return r.returncode, out
```

- [ ] 跑确认通过
- [ ] `git add adapters/zcode/gitcore.py adapters/tests/test_gitcore.py && git commit -m "T-026 gitcore 基础：仓库定位+执行封装+GitError"`

---

## Task 2 — gitcore 解析：status（porcelain v2）

**Files**
- Modify `adapters/zcode/gitcore.py`
- Modify `adapters/tests/test_gitcore.py`

**Interfaces**
- Produces:
  - `@dataclass FileStatus` — `path: str`、`index: str`、`worktree: str`、`staged: bool`、`untracked: bool`、`conflicted: bool`
  - `@dataclass RepoState` — `branch: str`、`upstream: str | None`、`ahead: int`、`behind: int`、`conflicts: list[str]`
  - `def git_status(root: Path) -> tuple[RepoState, list[FileStatus]]`

**解析规则（`git status --porcelain=v2 --branch`）**
- `# branch.head <branch>` / `# branch.upstream <up>` / `# branch.ab +<a> -<b>` → RepoState
- 条目 `1 <XY> ... <path>`（普通）/ `2 <XY> ...`（改名）/ `u <XY> ...`（未合并冲突）
- `staged = index != "."`；`untracked = worktree == "?"`；`conflicted = 条目前缀为 "u"` 或 XY 含 U

**步骤**

- [ ] 写失败测试（追加到 test_gitcore.py）：

```python
class TestGitStatus(GitCoreBase):
    def test_empty_repo_state(self):
        repo = self.make_repo()
        state, files = gitcore.git_status(repo)
        self.assertEqual(state.branch, "master")   # 默认 init 分支
        self.assertEqual(state.ahead, 0)
        self.assertEqual(files, [])

    def test_untracked_and_staged(self):
        repo = self.make_repo()
        (repo / "a.txt").write_text("hello", encoding="utf-8")
        _git(repo, "add", "a.txt")
        state, files = gitcore.git_status(repo)
        by_path = {f.path: f for f in files}
        self.assertTrue(by_path["a.txt"].staged)
        self.assertFalse(by_path["a.txt"].untracked)

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
```

- [ ] 跑确认失败（AttributeError：gitcore 无 git_status）
- [ ] 实现 `git_status`（含 v1 降级：git < 2.11 时用 `--porcelain` 单字母解析，code 先查 `git --version`）
- [ ] 跑确认通过；commit

---

## Task 3 — gitcore 解析：log / branch / stash / diff

**Files**
- Modify `adapters/zcode/gitcore.py`、`adapters/tests/test_gitcore.py`

**Interfaces**
- Produces:
  - `@dataclass CommitInfo` — `hash: str`、`parents: list[str]`、`author: str`、`date: str`、`subject: str`、`refs: str`
  - `@dataclass BranchInfo` — `name: str`、`is_local: bool`、`is_current: bool`、`upstream: str | None`
  - `@dataclass StashEntry` — `ref: str`、`message: str`
  - `def git_log(root: Path, n: int = 50) -> list[CommitInfo]`
  - `def git_branches(root: Path) -> list[BranchInfo]`
  - `def git_stash_list(root: Path) -> list[StashEntry]`
  - `def git_diff(root: Path, target: str | None = None, staged: bool = False) -> str`

**步骤**

- [ ] 写失败测试：`git_log` 用 `git log --format="%H%x00%P%x00%an%x00%ad%x00%s%x00%d"` 按 `\x00` 切字段；`git_branches` 用 `git branch -vv` + `git branch -r`；`git_stash_list` 用 `git stash list`；`git_diff` 用 `git diff [--cached] [--] target`
- [ ] 实现上述函数（`git_diff` 返回原文；解析失败抛 GitError）
- [ ] 跑确认通过；commit

---

## Task 4 — gitcore 写操作封装 + 危险命令识别

**Files**
- Modify `adapters/zcode/gitcore.py`、`adapters/tests/test_gitcore.py`

**Interfaces**
- Produces:
  - `DANGEROUS = ("reset --hard", "clean -f", "push --force", "checkout --")`
  - `def is_dangerous(args: list[str]) -> bool`
  - `def git_run(root: Path, args: list[str]) -> tuple[int, list[str]]` — 复用 run_git；非 0 时抛 GitError（code/out 携带）
  - 语义封装：`git_add(root, paths)`、`git_commit(root, message)`、`git_push/pull/fetch`、`git_checkout(root, ref)`、`git_merge(root, ref)`、`git_stash(root, action)`、`git_rebase(root, ref)`、`git_cherry_pick(root, ref)`、`git_tag(root, action, name)`、`git_remote(root, action, args)`、`git_reset(root, mode, ref)`、`git_revert(root, ref)` — 均返回 `tuple[int, list[str]]`，内部统一调用 `git_run`

**步骤**

- [ ] 写失败测试：`is_dangerous(["reset","--hard","HEAD~1"])` 为 True；`git_add` 后 `git status` 显示 staged；`git_commit` 成功返回 code 0 且 `git log` 出现提交；`git_run` 对不存在命令抛 GitError
- [ ] 实现；跑确认通过；commit

---

## Task 5 — gitcli：非 TTY 逐条命令 + 彩色渲染

**Files**
- Create `adapters/zcode/gitcli.py`
- Create `adapters/tests/test_gitcli.py`

**Interfaces**
- Consumes: `gitcore`（全部函数）
- Produces: `def run(argv: list[str]) -> int` — 分发 `status/log/diff/add/commit/push/pull/fetch/branch/checkout/merge/stash/rebase/cherry-pick/tag/remote/reset/revert`；`argv[0]` 为子命令名

**渲染约定**
- 彩色仅当 `sys.stdout.isatty()` 为 True；用 ANSI 常量（`RED = "\033[31m"`、`GREEN = "\033[32m"`、`YELLOW = "\033[33m"`、`CYAN = "\033[36m"`、`RESET = "\033[0m"`，不引入第三方）
- `status` 输出分组：`已暂存 / 未暂存 / 未跟踪`，每行 `<X><Y> <path>`；冲突文件标红
- 危险命令执行前打印 YELLOW 警告（`is_dangerous` 命中）

**步骤**

- [ ] 写失败测试：`run(["status"])` 在非 TTY（monkeypatch `sys.stdout` 为 StringIO）下输出含「未跟踪」且不含 ANSI 转义；`run(["log"])` 输出含提交 subject；危险命令警告路径测试
- [ ] 实现 `run()` + 各子命令渲染函数
- [ ] 跑确认通过；commit

---

## Task 6 — cli.py 注册 zcode git 入口（TTY 分发）

**Files**
- Modify `adapters/zcode/cli.py`

**Interfaces**
- Consumes: `gittui`、`gitcli`、`gitcore.find_git_root`
- 在 `main()` 的 subparsers 加：

```python
sp_git = sub.add_parser("git", help="git 仓库管理（TTY 进 TUI，非 TTY 逐条命令）")
sp_git.add_argument("raw", nargs=argparse.REMAINDER, help="子命令及参数（见 zcode git help）")
sp_git.set_defaults(func=cmd_git)
```

- `def cmd_git(args) -> int`：无 `args.raw` 且 `sys.stdout.isatty()` → `gittui.main()`；否则 `gitcli.run(args.raw)`；不在 git 仓库内时打印中文提示返回 1

**步骤**

- [ ] 写失败测试（test_gitcli 内或 cli 冒烟）：`zcode git status`（非 TTY）经 `main(["git","status"])` 返回 0；非仓库目录返回 1
- [ ] 实现 `cmd_git`（gittui 未实现前先 `import gittui` 留占位会失败——因此本任务与 Task 7 顺序执行：先写 Task 7 的 gittui 骨架 stub，再回来接通；计划执行顺序为 1→2→3→4→5→7→6→8→9→10）
- [ ] 跑确认通过；commit

---

## Task 7 — gittui：textual App 骨架 + Status 面板

**Files**
- Create `adapters/zcode/gittui.py`
- Modify `adapters/pyproject.toml`（`dependencies` 增加 `"textual"`）

**Interfaces**
- Consumes: `gitcore.git_status`、`gitcore.run_git`
- Produces: `def main() -> None` — `GitApp().run()`；`class GitApp(textual.app.App)`

**实现要点**
- `CSS`：左侧面板列表（`Vertical` 8 项高亮当前）、右侧内容 `DataTable`、底部状态栏 `Static`
- `BINDINGS`：`[("q", "quit", "退出"), ("tab", "next_panel", "切面板"), ("space", "toggle_stage", "暂存/取消"), ("d", "discard", "丢弃"), ("a", "stage_all", "全选"), ("question_mark", "help", "帮助")]`
- `compose()`：三块布局；`on_mount()` 刷新 `repo_status()` 填充 DataTable（列：状态/路径）+ 状态栏（分支·上游·变更数·冲突数）
- Status 面板选中行按 `space` → `gitcore.run_git(root, ["add", path])`（或 reset）后刷新

**步骤**

- [ ] 安装 textual：`.venv/bin/pip install textual`，真机验证 `import textual` 在 Python 3.14 成功
- [ ] 写 gittui 骨架（App + CSS + 空 DataTable + Status 面板刷新逻辑）
- [ ] 手动冒烟：TTY 下 `.venv/bin/zcode git` 进入界面，q 退出；非 TTY 不触发（由 Task 6 保证）
- [ ] 跑全量测试（gittui 无单测，靠冒烟）；commit

---

## Task 8 — gittui：Diff / Commit / Log 面板

**Files**
- Modify `adapters/zcode/gittui.py`

**步骤**

- [ ] Diff 面板：选中文件/提交 → `gitcore.git_diff` 结果渲染到 `Static`（`markdown=False`，原文高亮冲突标记）
- [ ] Commit 面板：`TextArea` 多行输入提交消息，`Ctrl+Enter` 提交 → `gitcore.git_commit` → 刷新 status
- [ ] Log 面板：`gitcore.git_log` → DataTable（hash/author/date/subject），回车显示详情 diff，`/` 触发过滤（`Input` 过滤 DataTable 行）
- [ ] 手动冒烟三项；commit

---

## Task 9 — gittui：Branch / Stash / Remote / 进阶面板 + 冲突解决

**Files**
- Modify `adapters/zcode/gittui.py`

**步骤**

- [ ] Branch 面板：`git_branches` 列表，回车 checkout，`n` 新建分支（弹 Input），`d` 删除，`m` 合并当前分支
- [ ] Stash 面板：`git_stash_list`，`p` pop、`a` apply、`d` drop、`s` 快速 stash
- [ ] Remote 面板：`git_fetch/pull/push` + 显示 ahead/behind
- [ ] 进阶面板：rebase / cherry-pick / tag / reset（soft/mixed/hard 三档 `ctx.ui` 确认）/ revert 的输入弹窗 + 危险确认
- [ ] 冲突解决：`repo_status()` 检测 `conflicts` 非空 → 状态栏「冲突:N」+ 自动高亮冲突文件；逐个文件选「保留本地(ours)/远端(theirs)/手动编辑」，执行 `git checkout --ours/--theirs -- <path>` 或打开编辑器；全部解决后提示 add + 继续 commit/rebase
- [ ] 手动冒烟：制造 merge 冲突 → 走完整解决流程；commit

---

## Task 10 — 文档同步 + 收尾

**Files**
- Modify `README.md`（快速开始加 `zcode git` 示例；目录结构加 gitcore/gitcli/gittui）
- Modify `AGENTS.md`（当前状态 + 构建/测试/部署加 git 子命令）
- Modify `CHANGELOG.md`（close 自动补录，无需手写）
- Modify `docs/UBIQUITOUS_LANGUAGE.md`（新术语：TUI / porcelain v2 / 冲突解决，用 `zcode ticket gloss add`）

**步骤**

- [ ] `zcode ticket gloss add TUI <定义>`、`porcelain v2`、`冲突解决` 三词条
- [ ] README / AGENTS 同步
- [ ] `zcode ticket phase review --green`；`zcode ticket transition T-026 review`；`zcode ticket resolve T-026 "..."`；`zcode ticket close T-026`

## 自审

- 规格覆盖：spec 第 4 节 8 面板 → Task 7/8/9；第 5 节命令映射 → Task 5；第 6 节数据模型 → Task 2/3；第 8 节测试 → 各任务测试周期。全对齐。
- 占位符：无。
- 类型一致：`FileStatus/RepoState/CommitInfo/BranchInfo/StashEntry` 在 Task 2/3 定义，Task 5/7/8/9 引用同名，无别名漂移。
