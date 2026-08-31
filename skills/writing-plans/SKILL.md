---
name: writing-plans
description: 写实现计划——把已批准的设计拆成文件结构清晰、bite-sized、每任务带测试周期的可执行计划。已有 spec、任务多步、接触代码之前使用。
---

# writing-plans — 写实现计划（标准版）

> 移植自 Superpowers 技能集。已有 spec / 需求、任务多步骤、**接触代码之前**使用。

## 何时使用

- 已完成 brainstorming（有已批准的设计文档）
- 任务是多步骤的、即将接触代码

## 工作流程

1. **宣告**：开头声明 "I'm using the writing-plans skill…"
2. **范围检查**：多独立子系统必须拆成多个计划（应在 brainstorming 阶段已拆）。
3. **文件结构**：先映射要创建/修改的文件及各自职责——边界清晰、一个文件一个职责、按职责而非技术层拆分、沿用既有模式。
4. **任务右尺寸**：任务是自带测试周期的最小单元，每个任务以独立可测的交付物结尾；配置/脚手架/文档折进需要它们的任务。
5. **bite-sized 粒度**：每步一个动作（2-5 分钟）：写失败测试 → 跑确认失败 → 最小实现 → 跑确认通过 → commit，全部 checkbox 语法。
6. **计划头模板**：Goal / Architecture / Tech Stack / **Global Constraints**（规格的项目级要求逐字复制，每任务隐含继承）。
7. **任务结构模板**：Files（Create/Modify/Test 精确路径）、Interfaces（Consumes/Produces 精确签名——任务实现者只看自己的任务）。
8. **自审**：规格覆盖（每个需求能指到任务）、占位符扫描、类型一致性（Task 3 叫 `clearLayers()` 而 Task 7 叫 `clearFullLayers()` 是 bug）。
9. **执行交接**：保存后给两个选项——Subagent-Driven（推荐：每任务新子代理 + 两阶段审查）或 Inline（批量执行 + 检查点）。

## 硬规则（No Placeholders）

- 禁止 "TBD / TODO / implement later"
- 禁止 "add appropriate error handling" 类空话
- 禁止 "write tests for the above"（必须附测试代码）
- 禁止 "Similar to Task N"（必须重复代码，工程师可能乱序读）
- 代码步骤必须给出实际代码块；假设工程师**零上下文且品味存疑**，一切写清楚
- DRY / YAGNI / TDD / 频繁提交

## 输出格式

- 计划文档：`docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`（完整可执行）

## 兜底

- 无 spec 就要求写计划 → 先返回 brainstorming
- 计划过大 → 拆成多个计划，每个保持 bite-sized
