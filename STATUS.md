# STATUS — 当前状态总览

> 由 zcode ticket status 自动生成，请勿手写。Agent 先读本文件即可了解全貌；细节按需再读对应文件。

## 关键状态
Phase: commit
Current Ticket: T-008
Domain: AI 技能运行时: 四层架构(适配层/技能库/编排工作流/记忆迭代), 中文文档, Python CLI 零依赖风格
TestCommand: .venv/bin/python -m unittest discover -s adapters/tests
BranchMode: auto
术语表: 2 条 (docs/UBIQUITOUS_LANGUAGE.md)

## 当前工单 T-008 (close 前文档同步强制: CHANGELOG 必须含工单号) [review]
## T-008 close 前文档同步强制: CHANGELOG 必须含工单号
Resolution: 根因: 文档同步靠事后追补(T-005 漏 CHANGELOG 被质疑), 无强制; 修复: close 守卫检查 CHANGELOG 含工单号(缺则拒), workbench/模板/AGENTS/README 同步文档同步条款, 新增 2 测试; 验证: 57 用例绿, 拒绝/放行路径测试覆盖
Status: review


## 工单
- [ ] **T-001** Phase 4: 其余平台深度插件 — backlog
- [ ] **T-002** Phase 4: 技能市场发布通道 — backlog
- [x] **T-003** 启用工单工作台于本仓库 — done  ✓已记录修复
- [x] **T-004** 同步 README 与 AGENTS.md 文档 — done  ✓已记录修复
- [x] **T-005** 测试补齐与回归防线 — done  ✓已记录修复
- [x] **T-006** 记录 CHANGELOG + 文档类改动不再阻塞 begin — done  ✓已记录修复
- [x] **T-007** 状态文件收尾入库 + 推送远程 — done  ✓已记录修复
- [ ] **T-008** close 前文档同步强制: CHANGELOG 必须含工单号 — review  ✓已记录修复

## 阻塞
(无)

<!-- GENERATED-BY-ZCODE -->