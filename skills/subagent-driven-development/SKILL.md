---
name: subagent-driven-development
description: 子代理驱动开发——每个任务派全新子代理（独立上下文），逐任务审查，最终全分支审查。当有实现计划且任务相互独立、宿主支持子代理工具时使用。
---

# subagent-driven-development — 子代理驱动开发（标准版）

> 移植自 Superpowers 技能集。假设宿主支持子代理工具（Kimi Code Agent / Claude Code Task / Codex spawn_agent 等，见工具映射表）。

## 何时使用

- 已有实现计划（writing-plans 产出）
- 任务大部分相互独立
- 宿主环境有子代理工具，且任务可在本会话内完成

## 工作流程

### 阶段 A：Setup
1. **隔离工作区**：不用 main 分支直接实现（git worktree 或独立分支）。
2. **建 ledger**：`.memory/sdd-ledger.md`，首行写计划身份；**检查既有 ledger**——标记 complete 的任务跳过，从第一个未完成处续跑（记忆恢复关键）。
3. **读计划 + 建 todos**：记下 Global Constraints，每个任务一个 todo。
4. **预检冲突扫描**：一次扫出计划内部矛盾，**批量**向用户提问"哪个说了算"，不中途逐条打断。

### 阶段 B：每任务循环
1. **记录 BASE**：`git rev-parse HEAD`（**绝不用 HEAD~1**，会丢多提交任务）。
2. **派遣实现者子代理**：构造**独立上下文**（文件传递，不粘会话历史）——一行位置说明 + 任务 brief 文件路径 + 之前任务产生的接口/决策 + 控制器对歧义的裁决 + 报告文件路径。**绝不并行派多个实现者**；**显式指定模型**。
3. **处理报告**（四态）：DONE → 审查；DONE_WITH_CONCERNS → 先解决正确性/范围问题；NEEDS_CONTEXT → 补上下文重派；BLOCKED → 四步评估（上下文→更强模型→拆小→计划错了上报用户）。
4. **任务审查（不可跳过）**：生成审查包（diff 文件）→ 派审查者（brief + 报告 + diff + Global Constraints）。审查者返回：**规格符合**（✅/❌/⚠️）+ **代码质量**（Approved/Needs fixes），每条带 `file:line`。**不信报告**——审查者对照 diff 核实。
5. **修复循环**：仅当 spec ❌ / Critical / Important 时触发，**每任务最多 5 轮**（第 1-3 轮恢复原实现者，第 4-5 轮换更强模型），每轮修复必须附测试证据。
6. **完成任务**：审查干净 → ledger 追加完成行 → 下一任务。

### 阶段 C：最终审查（全分支一次）
1. **派最强模型做全分支审查**（`git merge-base main HEAD` 起的完整 diff + ledger 遗留项）。
2. **只派 1 个修复子代理**处理全部发现（绝不一发现一修），跑**恰好一次**复审。
3. 残余 load-bearing 发现留给用户呈现，无第二次修复波。

### 阶段 D：收尾
- 审查干净且合并 → 清理工作区（git 历史即记录）→ 触发 code-review 收尾。

## 硬规则

- 子代理**独立上下文**：绝不继承会话历史；工件以文件传递
- 控制器**不做子代理的活**：不亲自写修复代码
- **审查不可跳过**：任务审查 + 最终审查两级；实现者自我审查不能替代
- **5 轮修复 cap**：超限即 breaker——控制器逐条裁决（审查者错了→park 落账；真实无下游→park 注明延期；**真实且 load-bearing→STOP 上报用户**），裁决必须落 ledger，禁止静默丢弃
- **不预判审查结果**：dispatch 里出现"不要标记 X"→ 停，你在预判
- 未经用户同意不在 main 上实现

## 输出格式

- ledger：`.memory/sdd-ledger.md`（任务状态/修复/park/BLOCKED 全部落账）
- 实现者报告：实现了什么 / 测试证据（RED+GREEN）/ 改动文件 / concerns
- 审查报告：Spec（✅/❌/⚠️）+ Issues（Critical/Important/Minor 带 file:line）+ Assessment

## 兜底

- 宿主无子代理工具 → 降级用 executing-plans（单代理逐任务执行，见 skills/executing-plans 或手动作业）
- 本地小模型当控制器 → 用本地精简版（skills/subagent-driven-development/SKILL.local.md），修复轮数降到 3
- 计划本身有缺陷 → STOP 上报用户，不硬编
