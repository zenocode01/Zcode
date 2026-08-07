# STATUS — 当前状态总览

> 由 zcode ticket status 自动生成，请勿手写。Agent 先读本文件即可了解全貌；细节按需再读对应文件。

## 关键状态
Phase: commit
Current Ticket: T-025
Domain: AI 技能运行时: 四层架构(适配层/技能库/编排工作流/记忆迭代), 中文文档, Python CLI 零依赖风格
TestCommand: .venv/bin/python -m unittest discover -s adapters/tests
BranchMode: auto
术语表: 14 条 (docs/UBIQUITOUS_LANGUAGE.md)

## 当前工单 T-025 (zcode update 自更新命令) [review]
## T-025 zcode update 自更新命令
Resolution: 根因: CLI 无自更新命令, 用户需手动 git pull + 重装多步; 实现: 新增 adapters/zcode/update.py + zcode update [--dry-run]——前置检查(工作区干净, 未提交改动拒绝防覆盖)→ git fetch(失败附网络/凭据提示)→ rev-list 已最新退出→ pull --ff-only→ 当前解释器 pip install -e→ npm link(可选, 失败仅警告)→ scripts/install.sh→ 变更摘要; 每步失败即停报告已完成步骤+重跑指引; 验证: 84 用例绿(新增 6: precheck 脏/净/dry-run 零执行/成功序列/已最新退出/失败中止), 真机 dry-run 与脏工作区拦截实测通过
Status: review

- [ ] - [ ] 实现: zcode update [--dry-run]——前置检查(仓库根/工作区干净/分支 main)→ git fetch 对比(已最新退出)→ git pull --ff-only → 当前解释器 pip install -e adapters → npm link(失败仅警告) → bash scripts/install.sh 刷新技能/钩子 → 输出变更摘要(git log 最近条目)
- [ ] 每步失败即停并报告已完成步骤与手动处理提示; 非 TTY 直接执行
- [ ] 验证: --dry-run 只打印不执行; 脏工作区拒绝; 更新后 zcode version/测试可用


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
- [ ] **T-025** zcode update 自更新命令 — review  ✓已记录修复

## 阻塞
(无)

<!-- GENERATED-BY-ZCODE -->