---
name: improve-arch
description: 架构治理——扫描代码库找"加深机会"（浅模块→深模块），HTML 报告呈现候选，逐项拷问决策。当用户要求改善代码库架构/可测试性时使用；仅用户主动调用。
---

# improve-arch — 架构治理（标准版）

> 移植自 Matt Pocock 技能集（improve-codebase-architecture）。仅用户主动调用（`disable-model-invocation`）。

## 何时使用

- 用户要求扫描代码库、改善架构、提升可测试性与 AI 可导航性
- 用户主动调用（模型不得自动触发）

## 工作流程

1. **Explore（范围先行，YAGNI）**：用户指定方向则用之；否则 `git log --oneline` 找热点路径优先；用探索子代理漫游，记录摩擦点（浅模块、为测试抽的纯函数但 bug 藏在调用处、跨 seam 泄漏、难测试处）；对疑似浅模块做 **deletion test**（删掉它是"集中复杂度"还是"只是搬走"——集中是想要的信号）。
2. **呈现候选为 HTML 报告**：写到 OS 临时目录 `<tmpdir>/architecture-review-<timestamp>.html`（**不落进仓库**）并打开；每个候选卡片含 Files / Problem / Solution / Benefits（用 locality + leverage 表述）/ Before-After 示意 / 推荐强度（Strong / Worth exploring / Speculative）；结尾给 Top recommendation。**硬规则：不要先提接口方案**，只问"你想探索哪个？"
3. **Grilling loop**：用户选一个候选后，走 grill-me 的决策树；新术语写进 `CONTEXT.md`、模糊术语当场修订、被拒候选有承重理由时提议记 ADR（防止未来重复建议）。

## 硬规则

- 架构词汇必须统一（module / interface / depth / seam / adapter / leverage / locality），禁止漂移到 "component / service / API / boundary"
- 先呈现问题与方向，不先给接口方案
- ADR 冲突仅在摩擦真实到值得重开时才提出

## 输出格式

- 报告：<tmpdir>/architecture-review-<timestamp>.html（不落仓库）
- 候选：Files / Problem / Solution / Benefits / 推荐强度
- 决策：<用户挑选的候选 + 深化结论>

## 兜底

- 无法打开浏览器 → 直接打印 HTML 路径给用户
- 用户对所有候选都不感兴趣 → 记录摩擦点，结束会话
