# STATUS — 当前状态总览

> 由 zcode ticket status 自动生成，请勿手写。Agent 先读本文件即可了解全貌；细节按需再读对应文件。

## 关键状态
Phase: commit
Current Ticket: T-028
Domain: AI 技能运行时: 四层架构(适配层/技能库/编排工作流/记忆迭代), 中文文档, Python CLI 零依赖风格
TestCommand: .venv/bin/python -m unittest discover -s adapters/tests
BranchMode: auto
术语表: 21 条 (docs/UBIQUITOUS_LANGUAGE.md)

## 当前工单 T-028 (zcode release 版本迭代工具) [review]
## T-028 zcode release 版本迭代工具
Resolution: 根因: 版本号散落五处人工维护+CHANGELOG 关单自动 bump 与代码版本脱节(0.3.16 vs 0.3.8)+marketplace.py 三处写死 0.1.0; 修复: 新增 release.py(zcode release patch/minor/major/X.Y.Z, 统一写五处版本号+归并未发布区块为正式版本+打 tag+可选 push)+marketplace.py 三处 0.1.0 改读 __version__+ticket._auto_changelog 改写未发布区块不再 bump+cli 注册 release; 验证: 123 用例全绿(新增 12 release), zcode release --dry-run 输出计划, marketplace build version=0.3.8, close 写未发布区块测试更新
Status: review

- [ ] 新增 zcode release 命令：统一 bump 五处版本号 + 对齐 CHANGELOG(未发布区块转正式版本) + 打 git tag + 可选推送；修复 marketplace.py 三处写死 0.1.0；改 close 逻辑不再每次 bump CHANGELOG 版本号


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
- [x] **T-023** install.sh 包装器生成逻辑修复: 优先项目 venv — done  ✓已记录修复
- [x] **T-024** zcode version 子命令 + __version__ 第五处版本统一 — done  ✓已记录修复
- [x] **T-025** zcode update 自更新命令 — done  ✓已记录修复
- [x] **T-026** zcode git 交互式 TUI 仓库管理 — done  ✓已记录修复
- [x] **T-027** pi-agent 插件三合一完整支持 — done  ✓已记录修复
- [ ] **T-028** zcode release 版本迭代工具 — review  ✓已记录修复

## 阻塞
(无)

<!-- GENERATED-BY-ZCODE -->