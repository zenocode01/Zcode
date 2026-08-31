---
name: brainstorming
description: 头脑风暴——任何创造性工作之前必须先使用：澄清问题、给 2-3 个方案带权衡、分节批准、写设计文档、转 writing-plans。未获批准前禁止写代码。
---

# brainstorming — 头脑风暴（标准版）

> 移植自 Superpowers 技能集。**任何创造性工作之前必须使用**（description 强约束，模型自动触发）。

## 何时使用

- 创建功能、构建组件、添加功能、修改行为的**任何创造性工作之前**（MUST use）
- 无论项目多简单（"太简单不需要设计"是反模式）

## 工作流程

1. **探索项目上下文**：文件、文档、近期提交。
2. **visual companion 恰到时机**：不 upfront；首次遇到"图示比描述清楚"的问题时才单独提议。
3. **澄清问题**：一次一个，聚焦 purpose / constraints / success criteria。
4. **提议方案**：2-3 个方案带权衡 + 你的推荐；YAGNI 无情削减。
5. **分节呈现设计**：按复杂度缩放（简单几行、复杂 200-300 字），**逐节征求批准**。
6. **写设计文档**：`docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` 并 git commit。
7. **规格自审**：占位符扫描 / 内部一致性 / 范围 / 歧义。
8. **用户审查**：用户审阅书面规格（修改则重跑自审）。
9. **转实现**：唯一可调用的下一技能是 writing-plans。

## 硬门（HARD-GATE）

- 呈现设计并获得用户批准前，**不得**调用任何实现技能、写代码、搭项目、采取任何实现行动

## 输出格式

- 设计文档：`docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`（已批准并提交）
- 终态：调用 writing-plans

## 兜底

- 多子系统请求 → 立即标记并先分解，每个子项目走独立 spec → plan → implementation 循环
- 用户急于写代码 → 明确告知硬门规则，给出最小可行的几句话设计供快速批准
