# Changelog

本项目从构思到四层架构落地（Phase 1-4）的变更记录。

## [0.2.0] - 2026-08-07

**新增**：工单驱动开发工作台（Layer 2，vibe-workbench 移植）——双状态机 + 可执行强制。

### 新命令（adapters/zcode/ticket.py + cli.py）
- `zcode ticket <cmd>`：init / add / begin / phase / transition / close / resolve / context / gloss / status / validate / next / log / install / projects / switch / project-add / ask / check-commit
- 两个状态机：Agent 阶段机（analyze→plan→implement→verify→review→commit）+ 工单生命周期机（backlog→in-progress→review→done，blocked→backlog）
- 可执行强制：阶段/流转守卫（非法跃迁拒绝）、依赖守卫与环检测、验证证据（TestCommand 真实执行 + `.vibe/evidence/` 留痕）、STATUS.md 状态自刷新与保鲜拦截、pre-commit hook 提交闸门、分支耦合（begin 自动开 `vibe/T-XXX`、close 自动 merge --no-ff 删除）
- 修复记录（`Resolution:` 锚点，close 前强制）与术语表（`vibe gloss add`，Domain 非空时强制非空）
- 兼容：与 vibe-workbench 文件格式（tickets.md / docs/CONTEXT.md / STATUS.md / `.vibe/`）与 `~/.vibe/projects.json` 注册表完全一致，两 CLI 可混用；STATUS 保鲜判定对生成器注释与 CRLF 行尾归一化

### 新技能与工作流
- `skills/workbench`（SKILL.md + SKILL.local.md）：工单驱动开发技能，入 ask-zcode 路由（匝道 + 独立技能 + 判别条件）
- `workflows/ticket-dev.yaml`：确定性工作流模板（workbench 技能 + context/next 命令 + 循环推进提示）

### 验证
- 端到端全流程：init → add → begin（自动开分支）→ phase 全链路（守卫拦截非法跃迁）→ transition → resolve → commit（pre-commit hook 拦截 Phase=analyze/in-progress 非法提交）→ close（校验 Resolution + 提交 + 自动合并分支）
- `zcode market validate` 12/12 通过

## [0.1.1] - 2026-08-06

**打磨**：EvoSkills 审计闭环修复 + tdd 技能首轮迭代（evoskills 六步循环实战）。

### 引擎修复（adapters/zcode/evoskills.py）
- 审计闭环缺陷：`needs_revision` 仅由历史成功率判定，发布修订版后成功率不变，导致"发布后重审计确认健康度回升"永远无法达成 → 新增 `_revision_published_since_last_issue()`：技能文件在最近失败/改进记录之后被修改过即视为已发布修订版，不再重复报修订，改为等待新样本
- 审计报告新增状态："✓ 已发布修订版，等待新样本"

### 技能迭代（skills/tdd）
- 审计触发：5 次使用 3 成功 2 失败、成功率 60% < 70%（教训：跳过测试直接改引入回归；没建反馈回路浪费两轮）
- 双版本补"启动门槛"：动手前确认反馈回路就绪；紧急修复先写复现测试、性能优化先写基准/特征测试，禁止跳过测试直接改

### 测试（首个测试框架落地）
- `adapters/tests/test_evoskills.py`：审计闭环 4 用例（unittest 零依赖，`python3 -m unittest discover -s adapters/tests`）

### 验证
- 4/4 测试通过；`zcode skill audit tdd` 显示已发布修订版；`zcode market validate` 全部通过

## [0.1.0] - 2025-08-06

**里程碑**：四层架构全部落地 + 真机端到端验证（Qwen3.6-35B / llama.cpp / 256K）。

### 技能库（Layer 1）
- 移植 10 个核心技能，全部**双版本**（`SKILL.md` 云 / `SKILL.local.md` 本地小模型）：
  - Matt Pocock 风格：`grill-me`（设计树拷问）、`tdd`（红绿重构）、`diagnose`（系统化调试）、`improve-arch`（架构治理）
  - Superpowers 风格：`brainstorming`（硬门）、`writing-plans`（No Placeholders）、`code-review`（分级反馈）
  - 自研：`handoff`（会话接力）、`subagent-driven-development`（子代理编排）、`evoskills`（自我迭代）
- `_template/` 双版本模板 + `.memory/` 技能级记忆模板（experience.log / improvements.md / context-snapshot.json）

### 适配层（Layer 0）
- Python 包 `zcode`：profile 能力声明、OpenAI 兼容 Provider（llama.cpp `/v1`）、工具三层降级（L2 原生 / L1 提示词编码 / L0 无工具）、工具映射表（spawn/parallel/todo/review → 8 平台）
- 8 平台适配：Claude Code / Cursor / Codex / Gemini CLI / opencode / Kimi Code / Pi / Reasonix（`INSTALL.md` + 软链接安装）
- `scripts/install.sh`：主目标 `~/.agents/skills`（跨工具事实标准）+ 平台原生目录双保险，幂等可卸载
- npm 分发入口（`bin/zcode.js` + `package.json`）

### 编排（Layer 2）
- 确定性工作流模板（`workflows/feature-dev`）：skill/prompt/command/subagent 四类步骤，外部 runner 驱动
- MetaSkill 自由编排（`metaskills/feature-dev`）：模型生成计划 → 复用执行器；profile `orchestration` 开关（本地默认 deterministic）
- 子代理编排：独立上下文 / ledger 恢复地图 / 逐任务审查（规格+质量）/ 5 轮修复 cap + breaker / 3 个提示词模板

### 记忆与迭代（Layer 3）
- mem0 本地三件套：Qwen3.6-35B（LLM）+ Qwen3-Embedding-8B（自定义 HttpEmbedder，4096 维）+ Qdrant 嵌入式
- 记忆写入四级降级（L0 纯 embedding → L1 简化提取 → L2 容错解析 → L3 批量）；检索零 LLM
- BM25 词形还原 + 实体增强（spaCy en_core_web_sm，经 gitproxy 代理解决国内网络）
- 会话接力：`zcode handoff save/load`（模板化六要素快照，不耗 token）
- EvoSkills 自我迭代：`zcode skill log/audit`（捕获/评估，阈值 70%/2 条）+ 六步循环元技能

### 生态（Phase 4 起步）
- 技能市场：`zcode market list/validate`（marketplace.json + 质量校验：frontmatter/命名/双版本/体积/占位符）
- 深度插件：Claude Code（`.claude-plugin/`）、opencode（permission.skill）、Kimi Code（installed.json）

### 真机验证（2025-08-06）
- 工具调用：tool_level=2（原生 tool calling）✅
- MetaSkill：真实模型自主编排（跳过 grill-me、遵守硬门）✅
- 记忆：add 提取 4 条事实 → search 命中 score 0.81 ✅
- 技能安装：10 技能软链到 `~/.agents/skills/`，幂等验证 ✅

### 关键修复
- L2 原生工具调用的 `tool_calls` 被 `Provider.chat()` 丢弃 → 新增 `chat_message()`
- mem0 provider 白名单校验 → `model_construct` 绕过
- mem0 2.0.17 API 差异（search 用 filters）→ 适配
- 记忆路径 `~` 未展开导致运行时数据误入仓库 → expanduser + `.gitignore` 防护
- 占位符校验误报（TODO vs todo、否定语境）→ 区分大小写 + 语境过滤
