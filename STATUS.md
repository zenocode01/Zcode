# STATUS — 当前状态总览

> 由 zcode ticket status 自动生成，请勿手写。Agent 先读本文件即可了解全貌；细节按需再读对应文件。

## 关键状态
Phase: commit
Current Ticket: T-020
Domain: AI 技能运行时: 四层架构(适配层/技能库/编排工作流/记忆迭代), 中文文档, Python CLI 零依赖风格
TestCommand: .venv/bin/python -m unittest discover -s adapters/tests
BranchMode: auto
术语表: 14 条 (docs/UBIQUITOUS_LANGUAGE.md)

## 当前工单 T-020 (close 流程健壮性修复: 中间态崩溃 + CHANGELOG 静默跳过) [review]
## T-020 close 流程健壮性修复: 中间态崩溃 + CHANGELOG 静默跳过
Resolution: 根因: ① cmd_close 在合并分支前执行 _auto_changelog 改 CHANGELOG.md, 而 repo_clean 只查非状态文件(CHANGELOG 在 STATE_PREFIXES 内), CHANGELOG 为分支独有文件时 git switch 被拒, close 中止在中间态(工单仍 review/条目已追加/分支未合并)且无恢复指引; ② _auto_changelog 文件缺失时直接 return None 不创建不提示, 与 SKILL.md 承诺不符; ③ repo_clean 命名误导(叫整仓干净实查源码); 修复: ① close 重排——先合并分支(switch 前预检 base 不存在的脏文件并阻止+指引, switch/merge 失败附恢复指引, 可幂等重跑)再补录 CHANGELOG; ② _auto_changelog 缺失时创建 [0.1.0] 基线并提示; ③ repo_clean 改名 dirty_source_paths 返回路径列表, 错误文案列具体文件; 验证: 68 用例绿(新增 Bug2 回归分支独有 CHANGELOG/预检脏文件, Bug3 基线创建, 函数改名 3 处)
Status: review


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
- [ ] **T-020** close 流程健壮性修复: 中间态崩溃 + CHANGELOG 静默跳过 — review  ✓已记录修复
- [ ] **T-021** gloss list 报「术语『list』不存在」应提示用法 — backlog

## 阻塞
(无)

<!-- GENERATED-BY-ZCODE -->