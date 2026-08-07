---
name: workbench
description: 工单驱动开发——用两个状态机（Agent 阶段机 + 工单生命周期机）+ 可执行强制管理 AI 工作流。当项目里有 tickets.md/docs/CONTEXT.md 工作台、用户提到"拾取工单"、"推进阶段"、"zcode ticket begin/phase/transition/close"、或要在工作台项目中规范地完成一段工作时使用。
---

# workbench — 工单驱动开发工作台

Zcode 的 Layer 2 工单驱动开发能力（移植自 vibe-workbench）。两个状态机把工作流变成硬规则：命令推进、守卫校验、状态自刷新、提交前强制拦截。

## 接手仓库：先看什么（省 token）

1. 先跑 `zcode ticket context`（或读 `STATUS.md`）：Phase / Current Ticket / 当前工单全文 / 依赖 / 最近流转，一屏足够开工。
2. 需要细节再按需读：`docs/UBIQUITOUS_LANGUAGE.md`（术语）、`docs/ADR/`（决策）、`docs/CONTEXT.md`（领域细节）。
3. 跨会话接力：`zcode handoff load` 拿会话级意图（目标/下一步）——与项目状态互补，不重复。
4. 不要一次性读完全部项目文件——按需读取，节省上下文。

## 两个状态机

### Agent 阶段机（运行时，你当前的位置）
```
analyze → plan → implement → verify → review → commit → analyze
    ↑        ↑        ↑          ↓        ↓
    └────────┴────────┴── verify失败 → implement
                         review打回 → implement
                         需求变化 → analyze
```

| 阶段 | 你要做什么 | 如何进入 |
|---|---|---|
| analyze | 理解领域，更新 `docs/CONTEXT.md` 的 `Domain:`；新术语用 `zcode ticket gloss add` 记录 | `zcode ticket begin T-XXX` |
| plan | 把工作拆成 tickets.md 工单 | `zcode ticket phase plan` |
| implement | 实现工单内容 | `zcode ticket phase implement` |
| verify | 运行验证产物，确认绿 | `zcode ticket phase verify` |
| review | 对照标准+规范自查 | `zcode ticket phase review --green` |
| commit | 提交代码并记录修复情况 | `zcode ticket phase commit --pass` |

守卫规则（脚本强制，不要绕过）：

- `analyze→plan`：需要 `Domain:` 非空
- `plan→implement`：需要 tickets.md 存在
- `implement→verify`：需要存在测试文件（`--force` 可跳过）
- `verify→review`：需要 `--green`（验证绿）
- `verify→implement`：需要 `--red`（验证红，即失败）
- `review→commit`：需要 `--pass`（审查通过）
- `review→implement`：需要 `--reject`（审查打回）

### 工单生命周期机（任务的持久状态）

```
backlog → in-progress → review → done
    ↑         ↑  ↖       ↓
    └─────────┴──── blocked → backlog
```

合法跃迁（`zcode ticket transition <t> <s>` 校验）：

| 当前 | 可去 |
|---|---|
| backlog | in-progress |
| in-progress | review, blocked |
| review | in-progress, done |
| blocked | backlog |

## 新增工单

用 `zcode ticket add [title]` 交互式新增（自动编号 T-XXX，可带标题跳过提问）。不要手写工单块。

## 修复记录（问题修复必须）

- 每个修复类工单在 close 前必须记录修复情况：`zcode ticket resolve T-XXX "根因: ...；修复: ...；验证: ..."`（写入工单块 `Resolution:` 锚点）。
- `zcode ticket close T-XXX` 强制校验 `Resolution:` 非空，否则拒绝关单。
- `zcode ticket validate` 也会检查 review 状态的工单是否缺少修复记录。

## 术语表（别漏）

- 遇到领域术语（歧义、专有名词、命名约定）立即 `zcode ticket gloss add <术语> <定义>`。
- `Domain:` 已填但术语表为空时，`zcode ticket validate` 和 pre-commit 都会拦截。

## 验证证据

- `docs/CONTEXT.md` 的 `TestCommand:`（如 `pytest`）配了之后，`zcode ticket phase verify` 会**真实执行**，退出码+输出写入 `.vibe/evidence/`；`--green` 仅在测试真跑绿放行，`--red` 仅在测试失败放行。
- `TestCommand:` 留空则退回自证 flag。

## 分支耦合（BranchMode: auto）

- `zcode ticket begin T-XXX` 自动从当前分支开 `vibe/T-XXX`（工作区有未提交改动会拒绝）。
- `zcode ticket close T-XXX` 校验当前分支有含 `T-XXX` 的提交，然后自动切回主分支 `merge --no-ff` 并删除 `vibe/T-XXX`。
- 冲突或脏工作区会中止 close，提示手动处理。
- 不想用自动分支：把 `docs/CONTEXT.md` 的 `BranchMode:` 改为 `manual`。

## 标准工作循环

1. `zcode ticket add "标题"`（可选）— 新增工单
2. `zcode ticket begin T-XXX` — 拾取工单（Phase=analyze，工单→in-progress，自动开分支）
3. `zcode ticket phase plan` → `zcode ticket phase implement` — 拆解并实现
4. `zcode ticket phase verify` — 跑测试；失败 `zcode ticket phase verify --red` 回 implement
5. `zcode ticket transition T-XXX review` — 实现完成，工单进 review（提交前必须完成）
6. `zcode ticket resolve T-XXX "根因+修复+验证"` — 记录修复情况（close 前必须）
7. `zcode ticket phase review --green` — 验证绿进审查
8. `zcode ticket phase commit --pass` — 审查过
9. git commit（pre-commit hook 校验：Phase 在 verify/review/commit、当前工单不在 in-progress、STATUS.md 保鲜、术语表非空、测试门禁）
10. `zcode ticket close T-XXX` — 关单（校验 Resolution + 已提交 → **自动补录 CHANGELOG（缺则加）→ 自动提交状态文件** → 合并分支 → Phase 复位）

> close 自动完成两件事，无需再开"收尾"工单：
> - **CHANGELOG 自动补录**：`CHANGELOG.md` 缺 `T-XXX` 时自动从 Resolution 生成条目（版本自动 bump）
> - **状态文件自动提交**：tickets.md / STATUS.md / CONTEXT / 术语表 / `.vibe/` / CHANGELOG 自动 commit（`T-XXX 状态收尾`），工作区保持干净

> 关键：工单必须在**提交前**流转到 review，修复记录必须在 close 前用 resolve 写好。若提交被拦提示 in-progress，先 `zcode ticket transition T-XXX review` 再提交。

## 文档同步（close 前必须）

**任何工单在 close 之前**，必须核对本次变更涉及的全部相关文件。工作台文件分两类，职责不同：

### A. 命令自动管理（无需人工，改了状态也会被保鲜/校验拦截）

| 文件 | 管理方式 |
|---|---|
| `tickets.md` | `zcode ticket add/begin/transition/resolve/close` 自动维护 |
| `STATUS.md` | 状态命令自动刷新；validate / pre-commit 发现过期直接拦截 |
| `docs/CONTEXT.md` | 仅 `Phase:`/`Current Ticket:` 等锚点由命令写；`Domain:`/`TestCommand:` 人工填 |
| `.vibe/`（log/evidence/meta/hooks） | 命令自动维护，随工单提交 |

> `docs/UBIQUITOUS_LANGUAGE.md`（术语表）：**写入**靠 `zcode ticket gloss add` 命令，但**何时登记由人工判断**——列入下方 B 表 close 前核对。

### B. 人工同步（close 前逐项核对，随工单一起 git commit）

| 文件 | 检查点 |
|---|---|
| **`CHANGELOG.md`** | **自动兜底**：缺本工单号时 close 自动从 Resolution 补录（版本自动 bump）；已有记录不重复 |
| `README.md` | 命令/能力/用例数/目录结构有变化时同步 |
| `AGENTS.md` | 当前状态（技能数/能力清单/仓库信息）、构建测试命令、协议条款有变化时同步 |
| **术语表 `docs/UBIQUITOUS_LANGUAGE.md`** | 本次工单引入的新术语是否已 `gloss add`（写入命令自动，登记决策人工——validate 只拦空表与格式，漏登记不会自动发现） |
| 技能清单 | 改 `skills/` 时：`ask-zcode` 路由、`skills/README.md`、`marketplace.json`（`zcode market validate` 通过） |

> CHANGELOG 与状态文件由 close 自动处理；README / AGENTS / 术语表 / 技能清单仍需人工核对后随工单提交，**不允许关单后文档未更新**。

## 建议下一步

不确定干什么时用 `zcode ticket next`：它会列出可拾取（依赖已 done）、依赖未满足（缺谁）、进行中/审查中的工单。

## 多项目

- `zcode ticket projects`：列出 `~/.vibe/projects.json` 里登记的项目及各自 Phase/当前工单。
- `zcode ticket switch <name>`：打印目标项目路径（bash/zsh 里 cd 过去）。
- `zcode ticket project-add <path>`：手动登记项目。

## 强制约束

- **绝不手动编辑** `Phase:`、`Status:`、`Current Ticket:`、`Domain:`、`Depends:`、`Resolution:`、`TestCommand:`、`BranchMode:` 锚点行。
- 状态文件的内容可以自由写，但锚点格式必须正确。
- 提交前跑 `zcode ticket validate`；pre-commit hook 会拦截非法提交（Phase 不在 verify/review/commit、当前工单还在 in-progress、STATUS.md 过期、Domain 已填但术语表为空）。
- 状态命令（begin/phase/transition/resolve/close/add）会自动刷新 STATUS.md；手动改了状态文件内容后记得跑 `zcode ticket status`。
- 依赖未满足的工单：`begin` 会拒绝，只可 `zcode ticket transition T-XXX blocked` 记阻塞，解除后回 `backlog` 重新排队。
- `BranchMode: auto` 时不要手动改分支。

## 与相邻能力的分工

| 系统 | 管什么 | 接手路径 |
|---|---|---|
| **workbench / zcode ticket** | 项目级实时状态：工单、阶段、验证证据、术语表（单一事实来源） | `zcode ticket context`（或读 STATUS.md） |
| **handoff** | 会话级接力：目标/下一步/决策结论；工作台项目"进行中"自动引用工单状态，不重复存 | `zcode handoff load`（会话开始）/ `save`（结束） |
| **mem0 / zcode memory** | 跨会话语义记忆：自由事实/偏好/经验，语义检索 | `zcode memory search <查询>` |
| 术语表 vs mem0 | 术语表=规范词条（校验强制）；mem0=自由事实（不强制） | — |
