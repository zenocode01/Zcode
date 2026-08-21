# STATUS — 当前状态总览

> 由 zcode ticket status 自动生成，请勿手写。Agent 先读本文件即可了解全貌；细节按需再读对应文件。

## 关键状态
Phase: commit
Current Ticket: T-026
Domain: AI 技能运行时: 四层架构(适配层/技能库/编排工作流/记忆迭代), 中文文档, Python CLI 零依赖风格
TestCommand: .venv/bin/python -m unittest discover -s adapters/tests
BranchMode: auto
术语表: 19 条 (docs/UBIQUITOUS_LANGUAGE.md)

## 当前工单 T-026 (zcode git 交互式 TUI 仓库管理) [review]
## T-026 zcode git 交互式 TUI 仓库管理
Resolution: 根因: zcode 无面向用户的 git 管理命令, git 能力仅内部使用(update/ticket/hooks); 修复: 新增 gitcore.py 零依赖逻辑层(status/log/branch/stash/diff 解析+写操作封装+危险命令识别) + gitcli.py 非 TTY 逐条命令彩色渲染 + gittui.py textual 全屏 TUI(8 面板+空格暂存+冲突 ours/theirs 解决) + cli.py 注册 TTY 分发 + pyproject 加 textual 依赖; 验证: 111 用例全绿(新增 21 gitcore+6 gitcli), textual 8.2.8 兼容 Python 3.14, TUI 冒烟 8 面板渲染+stage/unstage+冲突 ours 解决, 非 TTY zcode git status/log 正常
Status: review

- [ ] 新增 zcode git 子命令族：逻辑层 gitcore.py 零依赖封装 + textual TUI 全屏界面 + 非 TTY 逐条命令后备。面板覆盖 status/diff/commit/log/branch/stash/remote/rebase 进阶/cherry-pick/tag/reset/revert/冲突解决。


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
- [ ] **T-026** zcode git 交互式 TUI 仓库管理 — review  ✓已记录修复
- [x] **T-027** pi-agent 插件三合一完整支持 — done  ✓已记录修复

## 阻塞
(无)

<!-- GENERATED-BY-ZCODE -->