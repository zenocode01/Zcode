---
name: code-review
description: 代码审查——取 SHA 派审查子代理，反馈分级处理（Critical 立即修 / Important 修完再继续 / Minor 记下）。每个任务后、合并前必须使用。
---

# code-review — 代码审查（标准版）

> 移植自 Superpowers 技能集（requesting-code-review）。

## 何时使用

- **必须**：每个任务完成后、完成主要功能后、合并到 main 之前
- **可选**：卡住时（新视角）、重构前（基线检查）、修复复杂 bug 后

## 工作流程

1. **取 SHA**：`BASE_SHA`（如 HEAD~1 或 origin/main）与 `HEAD_SHA`。
2. **派审查子代理**：填充审查模板的 4 个占位符：`{DESCRIPTION}` / `{PLAN_OR_REQUIREMENTS}` / `{BASE_SHA}` / `{HEAD_SHA}`。
3. **处理反馈（分级）**：
   - **Critical**：立即修复
   - **Important**：修完再继续后续工作
   - **Minor**：记下稍后处理
   - reviewer 错了 → 带技术理由反驳（给代码/测试证据），要求澄清

## 核心原则

- 尽早评审、经常评审
- 给 reviewer **精确构建的上下文，绝不传你的会话历史**（diff 和评估都在 reviewer 上下文里，只有结论回来）
- 你是协调者：内联审查会烧掉你驱动后续工作的上下文

## 红旗（Red Flags）

- 禁止因"这很简单"跳过审查
- 禁止忽略 Critical
- 禁止带着未修的 Important 继续
- 禁止与有效技术反馈争论

## 输出格式

- 审查报告：Strengths / Issues（分级）/ Assessment
- 产出：修复后的代码

## 兜底

- 无 git 仓库 → 用 diff 文件替代 BASE_SHA/HEAD_SHA
- reviewer 不可用（本地小模型场景） → 降级为自查清单：逐文件核对关键路径、测试覆盖、边界条件
