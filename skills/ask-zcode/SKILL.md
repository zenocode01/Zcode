---
name: ask-zcode
description: 技能索引与路由——当任务匹配多个技能、或不确定该用哪个技能时使用。列出全部技能的 flow 地图与判别条件，先查这里再行动。
---

# ask-zcode — 技能索引与路由

> 移植自 Matt Pocock 技能集的 ask-matt：不是技能清单，而是**流程地图**——任务命名你的处境，地图把你放到流程的某一步。
> 机器清单（安装状态/校验）用 `zcode skills list` 与 `zcode market validate`；本技能是人工维护的决策地图。

## 何时使用

- 任务匹配多个技能，不确定该用哪个
- 用户问"该用哪个技能 / 有什么技能可用"
- 进入新任务前快速确认流程起点

## 主流程：想法 → 交付（功能开发）

```
grill-me（可选，仅用户调用：拷问需求）
    ↓
brainstorming —— 任何创造性工作之前：澄清 → 2-3 方案 → 分节批准 → 设计文档
    ↓（硬门：批准前禁止写代码）
writing-plans —— 拆成 bite-sized 计划（文件结构 + 每任务带测试）
    ↓
tdd —— 逐任务红绿重构
    ↓
code-review —— 分级反馈（Critical 立即修 / Important 修完再继续 / Minor 记下）
```

## 入口匝道（On-ramps）

| 情境 | 路由 |
|------|------|
| **报告 bug / 东西坏了 / 变慢** | `diagnose` → 紧致反馈回路 → 修复 + 回归测试；复盘发现是架构问题 → 移交 `improve-arch` |
| **代码库架构恶化 / 可测试性差** | `improve-arch`（仅用户调用）→ 扫描加深机会 → 逐项决策 |
| **有实现计划、任务相互独立、宿主支持子代理** | `subagent-driven-development` → 每任务独立子代理 + 逐任务审查 |
| **会话交接 / 新会话恢复上下文** | `handoff` → 会话开始 load、结束 save |
| **技能反复失败 / 质量下滑** | `evoskills` → audit → 达阈值生成改进版本 |

## 独立技能（Standalone）

- **`grill-me`**（仅用户调用）：与 brainstorming 的澄清不同——它是**无状态的拷问**，对已有计划/决定压力测试，挖沉默假设。有具体计划要拷问时用。
- **`brainstorming`** vs **`writing-plans`**：有想法无设计 → brainstorming；有设计无实现计划 → writing-plans。前者产出设计文档，后者产出可执行计划。

## 路由规则（判别条件）

1. **先命名你的处境**，不按关键词匹配——"功能开发"落在主流程起点（brainstorming 或已有设计则 writing-plans）；"修 bug"走 diagnose 匝道；"跨会话"走 handoff。
2. 不确定时**打开候选技能的 SKILL.md 读 description**，不凭本索引的一句话断言其行为（索引可能滞后）。
3. 用户主动点名（"用 grill-me"）时，尊重调用，即使本索引建议不同。

## 同步纪律（维护者必读）

- 新增/改名/删除技能时，**必须更新本索引**：主流程 / 匝道 / 独立技能三处对应关系
- 与 `marketplace.json`、`skills/README.md` 技能清单保持一致；`zcode market validate` 通过后才算完成
- 一个本索引从不提及的技能，或仍路由到已删技能，就是"撒谎的路由器"——立即修正

## 输出格式

- 路由结论：`→ <技能名>` + 一句话理由（为什么是这个而不是另一个）
- 涉及主流程时给出当前所处步骤与下一步

## 兜底

- 无技能匹配 → 明说"没有现成技能覆盖"，建议 brainstorming 生成新流程
- 本索引与技能实际内容矛盾 → 以技能 SKILL.md 为准，并标记索引待更新
