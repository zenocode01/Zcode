# zcode release 版本迭代工具 — 设计文档

- 日期：2026-08-21
- 状态：已批准（brainstorming 方案经用户确认）
- 关联工单：T-028

## 1. 背景与目标

zcode 版本号散落 5 处（`__init__.py`/`pyproject.toml`/`package.json`/`marketplace.json`/`.claude-plugin/plugin.json`），靠人工维护（T-019 手动统一过一次）；`zcode update`（T-025）只是自更新（git pull + 重装），不管理版本号；`marketplace.py` 三处写死 `0.1.0` 未同步；CHANGELOG 在关单时自动 bump 版本号，导致 CHANGELOG（0.3.16）与代码版本（0.3.8）脱节。

**目标**：新增 `zcode release` 命令，一次完成「统一 bump 版本号 → 对齐 CHANGELOG → 打 git tag → 可选推送」，并根治脱节。

## 2. 方案

### 2.1 版本号单一事实来源

`__version__`（`__init__.py`）为版本真相。release 时统一写入 5 处；`marketplace.py` 三处写死 `0.1.0` 改为 import `__version__`。

### 2.2 CHANGELOG 版本 = 发布版本（统一策略）

- **close 时**（改 `ticket._auto_changelog`）：不再 bump 版本号，改为把工单条目写入 CHANGELOG 顶部「未发布」区块；CHANGELOG 不存在时创建「未发布」基线。
- **release 时**：收集「未发布」区块条目 + 所有版本号 > 当前代码版本的历史条目（迁移遗留 0.3.9~0.3.16），归并成 `## [新版本] - 日期` 正式发布条目。

### 2.3 release 命令

```
zcode release [patch|minor|major|X.Y.Z] [--dry-run] [--push]
```

- bump 语义：patch/minor/major 按 semver 递增；或手动 `X.Y.Z`（须 > 当前版本）
- 前置检查：git 仓库 + 工作区干净（未提交改动拒绝）
- 流程：确定新版本 → 归并 CHANGELOG 未发布条目 → 写 5 处版本号 → `git add`+`commit`（`release vX.Y.Z`）→ `git tag vX.Y.Z` → 可选 `--push`（origin + tag）
- `--dry-run` 只打印计划不执行

## 3. 非目标（YAGNI）

- 不做 changelog 自动生成 from commits（沿用现有工单 Resolution 归并）。
- 不做多包/workspace 版本管理。
- 不做发布回滚。

## 4. 文件清单

```
adapters/zcode/release.py        # 新增：release 命令逻辑
adapters/zcode/marketplace.py    # 修改：三处 0.1.0 → __version__
adapters/zcode/ticket.py         # 修改：_auto_changelog 写「未发布」不再 bump
adapters/zcode/cli.py            # 修改：注册 release 子命令
adapters/tests/test_release.py   # 新增：release 测试
adapters/tests/test_ticket.py    # 修改：2 个 changelog 断言更新
README.md / AGENTS.md            # 修改：文档同步
```

## 5. 验收标准

1. `zcode release patch --dry-run` 打印计划不执行
2. `zcode release minor` 把 `__version__` 0.3.8 → 0.4.0，5 处版本号一致，CHANGELOG 归并未发布条目为 `## [0.4.0]`，打 tag `v0.4.0`
3. close 后 CHANGELOG 出现「未发布」区块而非新版本号
4. `zcode market generate` 不再产出 0.1.0
5. 全量测试绿（含新增 release 用例 + 更新后的 2 个 close 用例）
