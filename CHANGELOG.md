# Changelog

本项目从构思到四层架构落地（Phase 1-4）的变更记录。

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
