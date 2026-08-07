# STATUS — 当前状态总览

> 由 zcode ticket status 自动生成，请勿手写。Agent 先读本文件即可了解全貌；细节按需再读对应文件。

## 关键状态
Phase: commit
Current Ticket: T-021
Domain: AI 技能运行时: 四层架构(适配层/技能库/编排工作流/记忆迭代), 中文文档, Python CLI 零依赖风格
TestCommand: .venv/bin/python -m unittest discover -s adapters/tests
BranchMode: auto
术语表: 14 条 (docs/UBIQUITOUS_LANGUAGE.md)

## 当前工单 T-021 (gloss list 报「术语『list』不存在」应提示用法) [review]
## T-021 gloss list 报「术语『list』不存在」应提示用法
Resolution: 根因: ① cmd_add 条件反写——有参时取空串、无参才提问(dep_input/body), Depends 与描述参数静默丢失(登记工单时描述从未写入); ② gloss list 把 list 当术语查询报不存在, 查询未命中提示不完整; ③ add --help 把 --help 当标题建空单; 修复: ① 条件修正为有参取参、无参提问; ② gloss list/ls 识别为列出全部, 未命中提示完整用法(列出/添加); ③ run() 统一处理子命令 -h/--help 显示帮助, show_help 同步 add/gloss 用法; 验证: 72 用例绿(新增 4: add 依赖+描述写入/--help 不建单/gloss list 列出/未命中提示), 真机冒烟 add 带参写入成功
Status: review

- [ ] ① gloss list/ls 识别为列出全部（曾报「术语『list』不存在」）；查询未命中时提示完整用法（列出/添加）
- [ ] ② 附带发现: cmd_add 参数反写——有参时取空串，Depends/描述静默丢失（登记工单时描述全丢）
- [ ] ③ 附带发现: ticket add --help 把 --help 当标题建空单；统一子命令 --help 处理


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
- [ ] **T-021** gloss list 报「术语『list』不存在」应提示用法 — review  ✓已记录修复

## 阻塞
(无)

<!-- GENERATED-BY-ZCODE -->