---
name: ask-zcode
description: 技能索引（本地精简版）——不确定用哪个技能时先查地图。任务匹配多个技能时使用。
---

# ask-zcode（本地精简版）

## 何时使用

- 不确定该用哪个技能时

## 技能地图

主流程（功能开发）:
1. brainstorming → 设计（批准前不写代码）
2. writing-plans → 计划
3. tdd → 红绿重构实现
4. code-review → 审查分级

入口匝道:
- 修 bug → diagnose
- 架构差 → improve-arch
- 多任务独立执行 → subagent-driven-development
- 跨会话 → handoff
- 技能质量下滑 → evoskills
- 拷问计划 → grill-me（仅用户调用）

## 路由规则

1. 先命名处境，不按关键词匹配
2. 不确定时打开候选 SKILL.md 看 description
3. 用户点名用某技能 → 尊重

## 输出格式

- 路由: → <技能名> + 一句理由

## 兜底

- 无技能覆盖 → 建议 brainstorming 生成新流程
- 索引与技能矛盾 → 以 SKILL.md 为准
