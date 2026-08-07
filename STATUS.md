# STATUS — 当前状态总览

> 由 zcode ticket status 自动生成，请勿手写。Agent 先读本文件即可了解全貌；细节按需再读对应文件。

## 关键状态
Phase: commit
Current Ticket: T-022
Domain: AI 技能运行时: 四层架构(适配层/技能库/编排工作流/记忆迭代), 中文文档, Python CLI 零依赖风格
TestCommand: .venv/bin/python -m unittest discover -s adapters/tests
BranchMode: auto
术语表: 14 条 (docs/UBIQUITOUS_LANGUAGE.md)

## 当前工单 T-022 (memory add 静默 0 条: infer 提取失败自动降级 + 提示) [review]
## T-022 memory add 静默 0 条: infer 提取失败自动降级 + 提示
Resolution: 根因: MemStore.add 在 infer(simplified) 模式下直接透传 mem0, LLM 提取返回 0 条时静默返回空 results, CLI 只打印『已写入 0 条记忆』无任何提示/降级, 用户感知为写入失败且记忆丢失; 修复: ① MemStore.add 在 infer 且提取 0 条时自动降级 L0(原文纯 embedding 第二次写入, 参数透传), 返回 dict 附 degraded=True; ② CLI 检测 degraded 向 stderr 打印明确提示; 验证: 76 用例绿(新增 4: 降级两次调用/成功不降级/L0 不重试/CLI 提示), 真机 memory add 触发降级提示+写入成功; 已知环境限制: BM25 encoder 加载失败(fastembed 下载被 Steam++ 证书拦截), 检索降级纯 embedding 不影响核心
Status: review

- [ ] - [ ] 修复: MemStore.add 在 infer 提取返回 0 条时自动降级 L0(原文纯 embedding 写入, 记忆不丢), 返回带 degraded 标记; CLI 打印明确提示(提取失败/降级原因)
- [ ] 验证: mock mem0.add 两次调用(infer=True 空 → infer=False 成功), 全量测试绿; 真机 memory add 走降级路径写入成功
- [ ] 已知环境限制(不进本工单): BM25 encoder 加载失败——fastembed 从 HuggingFace 下载模型被 Steam++ 证书拦截(SSL_CERT_FILE 后下载源仍不可达), 检索降级为纯 embedding, 不影响核心功能


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
- [ ] **T-022** memory add 静默 0 条: infer 提取失败自动降级 + 提示 — review  ✓已记录修复

## 阻塞
(无)

<!-- GENERATED-BY-ZCODE -->