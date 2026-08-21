# zcode git 交互式 TUI 仓库管理 — 设计文档

- 日期：2026-08-21
- 状态：已批准（brainstorming 三节方案经用户确认）
- 关联工单：T-026
- 依赖：无

## 1. 背景与目标

当前 zcode 的 git 能力仅存在于内部（`update.py` 自更新、`ticket.py` 自动分支、`hooks/git-guard` 守卫），没有面向用户的 git 管理命令。用户需要一个"比 git 本身更直观易用、可视化"的仓库管理入口。

**目标**：新增 `zcode git` 子命令族，提供交互式全屏 TUI（对标 lazygit），覆盖核心日常 + 进阶 git 操作，并保留非 TTY 逐条命令后备。

## 2. 非目标（YAGNI 削减）

- 不重新实现 git 底层（submodule / worktree / bisect / notes / attributes 等不进 TUI）。
- 不做 Web UI、不做 GUI 桌面端。
- 不替代 git 本身——所有写操作仍委托 `git` CLI（`subprocess`），zcode 只做封装与展示。
- 不做多仓库并排管理（单仓库聚焦）。

## 3. 技术选型与架构

**TUI 库：`textual`**（方案 A，已批准）。理由：多面板/键盘绑定天然适配 lazygit 风格、官方有 `run_test` 测试工具、社区活跃。备选 urwid / prompt_toolkit 因开发效率或布局能力不足被否。

**分层架构（核心决策）**：

```
adapters/zcode/gitcore.py   # 纯逻辑层：subprocess 封装 git + 结构化解析，零第三方依赖
adapters/zcode/gittui.py    # 视图层：textual App，多面板 + 键盘绑定 + 中文提示
adapters/zcode/gitcli.py    # 非 TTY 后备：zcode git <子命令> 逐条命令 + 彩色输出
adapters/zcode/cli.py       # 注册 zcode git 子命令；TTY 进全屏 TUI，非 TTY 退逐条命令
```

关键原则：
1. **逻辑层零依赖、unittest 全测**——保持项目"零依赖可测"传统；textual 只在视图层出现，逻辑层测试不受污染。
2. **非 TTY 后备是刚需**——CI/管道/脚本无终端时 `zcode git status` 必须退化为逐条彩色输出（复用同一逻辑层）。
3. 视图层尽量薄——所有 git 语义、解析、错误归类放逻辑层；视图层只负责渲染与把键盘事件映射到逻辑层调用。

## 4. 功能面板与交互

**界面布局**：

```
┌────────────┬──────────────────────────────────┐
│ 状态 Status │  当前面板内容（文件列表 / 日志 /   │
│ 差异 Diff   │  diff / 分支 …）                  │
│ 提交 Commit │                                  │
│ 日志 Log    │                                  │
│ 分支 Branch │                                  │
│ 储藏 Stash  │                                  │
│ 远端 Remote │                                  │
│ 进阶 Rebase │                                  │
└────────────┴──────────────────────────────────┘
  [main] ↑2 ↓1  冲突:0   状态栏：分支·上游·变更数·冲突数
  Tab/1-8 切面板  ␣ 暂存  ? 帮助  q 退出
```

**8 个面板**：

| # | 面板 | 核心交互 |
|---|---|---|
| 1 | Status | 文件按 staged/unstaged/untracked 分组；`空格`=暂存/取消，`a`=全选，`d`=丢弃更改（带确认） |
| 2 | Diff | 选中文件或提交的 diff；冲突时高亮 `<<<<<<<`/`>>>>>>>` 标记 |
| 3 | Commit | 暂存区概览 + 多行消息编辑器；提交前可选跑 pre-commit |
| 4 | Log | ASCII 分支图 + 提交历史；`/` 过滤，回车看详情，支持 reset/revert/cherry-pick 选中提交 |
| 5 | Branch | 本地/远程分支；checkout/新建/删除/重命名/合并 |
| 6 | Stash | 列表 + pop/apply/drop；`s` 快速 stash |
| 7 | Remote | fetch/pull/push；显示落后/领先提交数 |
| 8 | 进阶 | Rebase（交互式）、Cherry-pick、Tag、Reset（soft/mixed/hard 三档确认）、Revert |

**冲突解决流程（重点）**：merge/rebase 产生冲突时，状态栏显示「冲突:N」并自动高亮进入 Diff 面板 → 逐个冲突文件选「保留本地(ours) / 保留远端(theirs) / 手动编辑」→ 全部解决后提示 `add` + 继续 commit/rebase。

**全局交互**：`?` 帮助、`Tab`/数字键切面板、`q` 退出、`/` 搜索。底部状态栏实时显示分支、上游、未提交数、冲突数。

## 5. 非 TTY 命令映射

```
zcode git                 # 无参数 = 进全屏 TUI（非 TTY 则打印帮助）
zcode git status          # 彩色状态（分组 + 短状态码）
zcode git log [--graph]   # 提交历史 / ASCII 分支图
zcode git diff [path]     # 差异
zcode git add <path...>   # 暂存（支持 -A）
zcode git commit [-m msg] # 提交（无 -m 时在 TTY 用编辑器）
zcode git push|pull|fetch [remote] [branch]
zcode git branch [-a] [name]
zcode git checkout <ref>
zcode git merge <ref>
zcode git stash [list|pop|apply|drop]
zcode git rebase <ref> [-i]
zcode git cherry-pick <ref>
zcode git tag [list|add|delete]
zcode git remote [list|add|remove|set-url]
zcode git reset [--soft|--mixed|--hard] <ref>
zcode git revert <ref>
```

非 TTY 输出统一走 `gitcli.py` 的彩色渲染（复用 gitcore 的结构化结果），危险命令（reset --hard、clean、强制 push）打印警告提示。

## 6. 逻辑层数据模型（gitcore）

零第三方依赖，返回结构化数据供视图层/命令行层共用：

| 结构 | 字段 | 来源 |
|---|---|---|
| `FileStatus` | `path` / `index`(X/Y 状态码) / `worktree` / `staged` / `untracked` / `conflicted` | `git status --porcelain=v2` |
| `RepoState` | `branch` / `upstream` / `ahead` / `behind` / `conflicts` | `git status --branch --porcelain=v2` |
| `CommitInfo` | `hash` / `parents` / `author` / `date` / `subject` / `refs` | `git log --format` |
| `BranchInfo` | `name` / `is_local` / `is_current` / `upstream` | `git branch -vv` + `git branch -r` |
| `StashEntry` | `ref` / `message` | `git stash list` |

写操作函数（`add/commit/push/pull/fetch/checkout/merge/stash/rebase/cherry-pick/tag/remote/reset/revert`）统一封装为「返回 `(code, output)`，错误归类为中文提示」的薄包装。

## 7. 目录与文件清单

```
adapters/zcode/gitcore.py            # 新增：逻辑层（零依赖）
adapters/zcode/gitcli.py             # 新增：非 TTY 逐条命令 + 彩色输出
adapters/zcode/gittui.py             # 新增：textual TUI 视图
adapters/zcode/cli.py                # 修改：注册 git 子命令
adapters/pyproject.toml              # 修改：dependencies 加 textual
adapters/tests/test_gitcore.py       # 新增：逻辑层 unittest（临时仓库夹具）
adapters/tests/test_gitcli.py        # 新增：命令映射/渲染（可选，非 TTY 部分）
README.md / AGENTS.md / CHANGELOG.md # 修改：文档同步（随工单）
```

## 8. 测试策略

- **gitcore 用 unittest + 临时 git 仓库夹具**（`tempfile.TemporaryDirectory` + `git init` + 造提交/分支/冲突），覆盖 status 解析、log 解析、分支解析、冲突检测、写操作错误归类。零依赖，与现有 `python3 -m unittest discover -s adapters/tests` 兼容。
- **视图层**：textual 提供 `run_test`（headless 测试），对关键交互（切面板、stage/unstage、退出）做冒烟；深度 UI 行为以手动验证为主，不追求 UI 全覆盖。
- **回归**：现有 84 用例不受影响；新增 gitcore/gitcli 用例并入测试门禁（TestCommand）。

## 9. 验收标准

1. `zcode git` 在 TTY 下进入全屏 TUI，8 面板可用，中文提示。
2. 核心日常（status/stage/commit/push/pull/branch/checkout/merge/log/diff/stash）+ 进阶（rebase/cherry-pick/tag/remote/reset/revert/冲突解决）可完成。
3. 非 TTY 下 `zcode git status|log|diff|...` 退化为逐条彩色输出，不崩溃。
4. `python3 -m unittest discover -s adapters/tests` 全绿（含新增 gitcore 用例）。
5. 冲突解决流程：merge 冲突 → 状态栏「冲突:N」→ 逐个选 ours/theirs/手动 → 全部解决后继续。

## 10. 风险与权衡

| 风险 | 缓解 |
|---|---|
| textual 依赖较重，与"轻量"哲学有张力 | 逻辑层零依赖、视图层隔离；textual 仅 dev/runtime 依赖视图层 |
| textual 对 Python 3.14 的兼容性 | 实现时选兼容版本并真机验证；不兼容则回退 urwid（分层架构不变） |
| git 输出格式跨版本差异（porcelain v2 需 git ≥ 2.11） | 检测 git 版本，过低时降级 porcelain v1 解析 |
| 写操作误触（reset --hard 等） | 危险命令统一二次确认；非 TTY 打印警告 |
| 大仓库 log/status 渲染卡顿 | 列表虚拟滚动（textual 内建），log 默认限量分页加载 |
