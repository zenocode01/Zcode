# STATUS — 当前状态总览

> 由 zcode ticket status 自动生成，请勿手写。Agent 先读本文件即可了解全貌；细节按需再读对应文件。

## 关键状态
Phase: commit
Current Ticket: T-023
Domain: AI 技能运行时: 四层架构(适配层/技能库/编排工作流/记忆迭代), 中文文档, Python CLI 零依赖风格
TestCommand: .venv/bin/python -m unittest discover -s adapters/tests
BranchMode: auto
术语表: 14 条 (docs/UBIQUITOUS_LANGUAGE.md)

## 当前工单 T-023 (install.sh 包装器生成逻辑修复: 优先项目 venv) [review]
## T-023 install.sh 包装器生成逻辑修复: 优先项目 venv
Resolution: 根因: install.sh 的 install_cli 写死 exec python3(系统解释器), 且包检查基于系统 python3; 重跑 install.sh 会覆盖手工修好的 venv 包装器(Bug 1 复发, ModuleNotFoundError); 修复: 解释器优先 REPO_ROOT/.venv/bin/python(PEP 668 环境), 回退 python3; 包装器与检查逻辑同步用实际解释器; 验证: 重跑 install.sh 后包装器指向 venv 且任意目录 zcode 可用(无 ModuleNotFoundError), 76 用例全绿
Status: review

- [ ] - [ ] 修复: install.sh 生成 CLI 包装器时写死 exec python3(系统解释器), 重跑 install.sh 会覆盖已修好的 venv 包装器(Bug 1 复发); 改为优先 REPO_ROOT/.venv/bin/python(PEP 668 环境必须 venv), 回退 python3; 包检查逻辑同步用实际解释器
- [ ] 验证: 重跑 install.sh 后包装器指向 venv, 任意目录 zcode 可用, 无 ModuleNotFoundError


## 工单
- [ ] **T-001** Phase 4: 其余平台深度插件 — backlog
- [ ] **T-002** Phase 4: 技能市场发布通道 — backlog
- [x] **T-003** 启用工单工作台于本仓库 — done  ✓已记录修复
- [x] **T-004** 同步 README 与 AGENTS.md 文档 — done  ✓已记录修复
- [x] **T-005** 测试补齐与回归防线 — done  ✓已记录修复
- [x] **T-006** 记录 CHANGELOG + 文档类改动不再阻塞 begin — done  ✓已记录修复
- [x] **T-007** 状态文件收尾入库 + 推送远程 — done  ✓已记录修复
- [x] **T-008** close 前文档同步强制: CHANGELOG 必须含工单号 — done  ✓已记录修复
- [x] **T-009** 文档同步清单完整化: 六文件职责分类 + 修欠账 — done  ✓已记录修复
- [x] **T-010** close 自动化: 状态文件自动提交 + CHANGELOG 自动生成, 消灭收尾/欠账工单 — done  ✓已记录修复
- [x] **T-011** 三系统分工: handoff×mem0×workbench 去重联动 — done  ✓已记录修复
- [x] **T-012** 通俗版使用说明: 面向非技术读者的功能与框架说明 — done  ✓已记录修复
- [x] **T-013** 术语表欠账补齐 + 登记时机改为 close 前人工核对 — done  ✓已记录修复
- [x] **T-014** 普通用户实操手册: 零基础照做指南 — done  ✓已记录修复
- [x] **T-015** 上手体验优化: init 交互引导 + --existing 自动并入协议 + CLI 全局安装 — done  ✓已记录修复
- [x] **T-016** Windows 跨平台支持: install.ps1 + hook 宿主适配 + 测试/文档 — done  ✓已记录修复
- [x] **T-017** pwsh 真机验证 install.ps1 + 修复路径 bug — done  ✓已记录修复
- [x] **T-018** 完整测试发现的 3 个缺陷修复 — done  ✓已记录修复
- [x] **T-019** 正式发布 0.3.8: 版本统一 + Release — done  ✓已记录修复
- [x] **T-020** close 流程健壮性修复: 中间态崩溃 + CHANGELOG 静默跳过 — done  ✓已记录修复
- [x] **T-021** gloss list 报「术语『list』不存在」应提示用法 — done  ✓已记录修复
- [x] **T-022** memory add 静默 0 条: infer 提取失败自动降级 + 提示 — done  ✓已记录修复
- [ ] **T-023** install.sh 包装器生成逻辑修复: 优先项目 venv — review  ✓已记录修复

## 阻塞
(无)

<!-- GENERATED-BY-ZCODE -->