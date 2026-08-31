---
name: handoff
description: 会话接力（本地精简版）——开始读快照恢复上下文，结束存快照。每次会话开始/结束时使用。
---

# handoff（本地精简版）

## 何时使用

- 会话开始时：读快照恢复
- 会话结束时：存快照

## 工作流程

1. 开始：运行 zcode handoff load
2. 有快照 → 恢复目标/进行中/决策/验证/下一步
3. 关键决策和验证结果发生时记下
4. 结束：运行 zcode handoff save，填六要素
   - --goal: 目标
   - --achieved: 已完成
   - --in-progress: 进行中
   - --decisions: 决策（含原因）
   - --validation: 验证结果
   - --next: 下一步

## 输出格式

- 快照: <项目>/.memory/handoff.md（或 --global）

## 兜底

- 无快照 → 说"无接力快照"，不编造
- 保存失败 → 报路径，改全局存储
