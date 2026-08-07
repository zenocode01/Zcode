---
name: workbench
description: 工单驱动开发（本地精简版）——两个状态机推进工作：begin 拾取→phase 阶段→transition 流转→resolve 记录→close 关单。项目里有 tickets.md 时使用。
---

# workbench（本地精简版）

## 何时使用

- 项目里有 tickets.md / docs/CONTEXT.md
- 用户要求拾取工单、推进阶段、关单

## 接手先看

1. `zcode ticket context`（或读 STATUS.md）一屏拿全貌
2. 细节按需读，不全量加载

## 工作流程

1. 无进行中工单 → `zcode ticket next` 看可拾取项
2. `zcode ticket begin T-XXX` 拾取（自动开分支）
3. `zcode ticket phase plan` → `implement` 实现
4. `zcode ticket phase verify` 验证（绿 `--green`，红 `--red` 回 implement）
5. `zcode ticket transition T-XXX review`
6. `zcode ticket resolve T-XXX "根因+修复+验证"`
7. `zcode ticket phase review --green` → `commit --pass`
8. 更新相关文档（CHANGELOG 必须含 T-XXX；README/AGENTS/技能清单按需）
9. git commit 后 `zcode ticket close T-XXX`

## 硬规则

- 绝不手动改 `Phase:`/`Status:`/`Current Ticket:`/`Domain:`/`Resolution:` 锚点
- close 前必须 resolve；Domain 填了术语表必须非空
- 有 CHANGELOG.md 时 close 前必须已记录本工单号（守卫强制）
- 状态命令自动刷新 STATUS.md；tickets/STATUS/CONTEXT 归命令管，不用人工

## close 前文档核对

- 自动管（不用动）：tickets.md / STATUS.md / CONTEXT 锚点 / 术语表 / .vibe
- 人工管（随工单提交）：CHANGELOG 必须含 T-XXX（强制）；README/AGENTS/技能清单按变更同步

## 兜底

- 提交被拦 → 看报错：Phase 未到 verify/review/commit 先 phase verify；工单 in-progress 先 transition review；STATUS.md 过期先 status
- 不确定 → `zcode ticket ask <话题>` 路由
