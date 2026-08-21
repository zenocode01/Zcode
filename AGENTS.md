# AGENTS.md — Zcode 项目指南

本文件供 AI 编码代理阅读。阅读者应对项目一无所知,请先完整阅读本文件,再进入项目操作。

## 项目概述

**Zcode**(仓库路径:`ZENO/Zcode/Zcode-0.0`)的目标是构建一个 **AI 技能的"操作系统"**——一套轻量的、可插拔的"技能运行时环境",而非另一个重型框架。核心理念:将 AI 技能从"一次性指令"升级为"可安装、可组合、可记忆、可进化"的能力产品。

设计哲学借鉴两个开源项目:
- **Matt Pocock 的技能集**:"小、可组合、随时可改",每个技能是独立的 Markdown 指令集,像乐高积木
- **Superpowers**:"强制工作流",通过启动时注入引导上下文,让 Agent 先查技能再行动

最终效果:只需维护一个技能仓库,就能在任意 AI 工具(Claude Code、Cursor、Codex、Gemini CLI 等)中获得一致的工作流能力,且能力随使用不断进化和记忆。

## 当前状态(重要)

> **Phase 1/2/3 核心能力全部落地(2026-08):技能库、适配层、8 平台安装、工作流/编排、工单驱动工作台、子代理驱动开发、记忆层(mem0)真机验证、会话接力。**

- 需求与设计文档:
  - `docs/基本构思.md` —— 唯一权威需求来源(四层架构 + 本地小模型优化定稿 + 路线图),开发前务必先读
- 已落地:
  - `skills/` —— 技能库,双版本(`SKILL.md` 云 / `SKILL.local.md` 本地),12 个技能(grill-me/brainstorming/writing-plans/tdd/diagnose/code-review/improve-arch/handoff/subagent-driven-development/evoskills/workbench/ask-zcode) + `_template/` 模板(含 `.memory/` 记忆模板)
  - `adapters/` —— Python 包 `zcode`(profile/Provider/工具三层降级/MemStore/CLI/工具映射表/gitcore/gitcli/gittui/release)、`profiles/local-qwen3.6-35b.yaml`、8 平台 `platforms/*/INSTALL.md`
  - `workflows/` —— 确定性工作流模板(Layer 2):`feature-dev` / `ticket-dev` + 引擎(支持 skill/prompt/command/subagent 步骤)
  - 工单驱动工作台(Layer 2,移植 vibe-workbench):`zcode ticket` 命令族(init/add/begin/phase/transition/close/resolve/context/gloss/status/validate/next/log/install/projects/switch/ask)——双状态机(Agent 阶段机 + 工单生命周期机) + 可执行强制(守卫/依赖环检测/验证证据/STATUS 自刷新/pre-commit 闸门/自动分支) + `skills/workbench` 技能;与 vibe-workbench 文件格式与注册表兼容,两 CLI 可混用
  - `metaskills/` —— MetaSkill 自由编排(Layer 2):模型生成计划 + 复用执行器
  - 记忆层(Phase 3):`zcode memory add/search/list`(mem0 + 自定义 HttpEmbedder 对接 Qwen3-Embedding-8B + Qdrant 本地),BM25/实体增强已启用(spaCy),真机端到端验证通过
  - 会话接力:`zcode handoff save/load` + `skills/handoff`(模板化快照,不依赖历史聊天)
  - 子代理编排:`skills/subagent-driven-development`(独立上下文/ledger/逐任务审查/5轮修复cap) + 3 个提示词模板 + `zcode tools list` 工具映射表
  - 自我迭代(EvoSkills):`zcode skill log/audit`(捕获使用记录/评估健康度,阈值 70%/2条) + `skills/evoskills` 元技能(监控→捕获→评估→迭代→验证→发布)
  - 技能市场与质量评估(Phase 4 起步):`zcode market list/validate/generate` + `marketplace.json` + `.claude-plugin/`(Claude Code 深度插件,参考 mem0 格式) + Pi 深度插件(`adapters/platforms/pi/extension/`：`/zcode` 命令透传 + `zcode_*` 只读工具 + Pi Package 打包,见 `adapters/platforms/pi/INSTALL.md`)
  - `scripts/install.sh` —— 跨平台一键安装;`hooks/` —— git 安全守卫;`bin/zcode.js` + `package.json` —— npm 分发入口
- Git 仓库已有提交(`main` 分支);远程 `origin` 指向 `https://github.com/zenocode01/Zcode.git`
- 尚未实现:技能市场远程分发与社区贡献、其余平台深度插件(cursor/codex/gemini 等,pi 已落地)、技能市场发布

任何 AI 代理在本仓库中的工作,都应从推动"实施路线图"的下一步开始,而不是假设已有功能。

## 目标架构:四层设计

```
┌─────────────────────────────────────────────────────────────┐
│                    统一工作流集 (Meta-Framework)              │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: 自我迭代与记忆层（Meta-Skills + 记忆系统）          │
│  - 技能自我进化（EvoSkills / task-observer）                 │
│  - 技能级记忆（Acontext / skill-evo）                       │
│  - 会话接力与项目记忆（agent-handoff-skill）                │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: 技能编排与工作流层（Workflow Engine）              │
│  - 工作流模板（MetaSkill）                                  │
│  - 子代理编排（subagent-driven-development）                │
│  - 跨技能依赖与触发规则                                     │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: 核心技能库（Core Skills）                         │
│  - Matt Pocock 风格：grill-me, tdd, diagnose, improve-arch  │
│  - Superpowers 风格：brainstorming, writing-plans, code-review│
│  - 自定义扩展技能                                           │
├─────────────────────────────────────────────────────────────┤
│  Layer 0: 跨平台适配层（Adapter Layer）                     │
│  - 工具映射（tool mapping）                    │
│  - 插件格式转换（Claude/Cursor/Codex/Gemini...）│
│  - 软链接桥接（ai-skill-link）                  │
└─────────────────────────────────────────────────────────────┘
```

### Layer 0:跨平台适配层 —— 实现"即插即用"

- 统一技能格式:以 Anthropic 的 Agent Skills 开放标准为基础,所有技能用 `SKILL.md` 封装
- 工具映射表:将不同平台的工具调用映射到统一接口(如 Claude 的 `Task` → Codex 的 `spawn_agent`;Claude 的 `TodoWrite` → Codex 的 `update_plan`)
- 软链接桥接:通过 `ai-skill-link` / `Skiller` 将技能仓库软链接到各平台技能目录
- 交付物:`install.sh` 脚本 + 各平台的 `plugin.json` / `INSTALL.md` 适配文件

### Layer 1:核心技能库 —— 实现"可复用"

按"失败模式"组织技能(即:每个技能解决一个具体的翻车场景),初始清单:

| 类别 | 技能 | 说明 |
|------|------|------|
| 需求对齐 | `grill-me` / `grill-with-docs` / `brainstorming` | 先拷问再编码 |
| 规划 | `writing-plans` | 写实现计划 |
| 测试驱动 | `tdd` / `test-driven-development` | 红绿重构 |
| 调试 | `diagnose` / `systematic-debugging` | 系统化诊断 |
| 代码审查 | `requesting-code-review` | 强制审查 |
| 架构治理 | `improve-codebase-architecture` | 防止代码熵增 |
| 子代理 | `subagent-driven-development` | 并行分工 |

关键设计原则:技能之间松散独立、可随意组合;Agent 在合适语境下自动加载(model-invoked)。

### Layer 2:技能编排与工作流层 —— 实现"可扩展"

- **MetaSkill(元技能)**:不写固定流程,把规则和可用技能告诉模型,由模型自行编排流程(文档中有完整示例)
- **工作流模板**:将多个子技能的执行流程打包成可复用模板,支持参数传递、错误兜底
- **子代理编排**:多个 Agent 并行/分工执行,主 Agent 负责审查与协调

### Layer 3:自我迭代与记忆层 —— 实现"自我迭代"与"记忆"

- **技能级记忆**:每个技能目录下维护 `.memory/` 文件夹——`experience.log`(使用经验)、`improvements.md`(改进建议)、`context-snapshot.json`(项目上下文快照)
- **自我迭代循环**:监控 → 捕获 → 评估 → 迭代 → 验证 → 发布(只有评分达阈值才发布)
- **会话接力**:`agent-handoff-skill` 在会话间建立连续性记忆,让未来 Agent 恢复目标、状态、决策、验证结果,不依赖历史聊天记录

## 实施路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 1:基础框架(1-2 周) | 创建统一技能仓库结构(`skills/`、`hooks/`、`adapters/`);跨平台适配层;一键安装脚本;移植 Matt Pocock 与 Superpowers 核心技能 | 未开始 |
| Phase 2:编排与工作流(2-3 周) | MetaSkill 引擎;工作流模板系统;子代理编排;示例工作流(功能开发、Bug 修复、代码重构) | 未开始 |
| Phase 3:记忆与迭代(3-4 周) | 集成 Acontext 或自建记忆层;skill-evo 风格经验回写;会话接力;EvoSkills 自我迭代循环 | 未开始 |
| Phase 4:生态与社区(持续) | 开放技能/插件市场;社区技能包;技能质量评估体系 | 未开始 |

## 关键技术选型(构思文档中的建议)

| 组件 | 推荐方案 | 理由 |
|------|----------|------|
| 技能格式 | Anthropic Agent Skills 标准 | 最广泛兼容 |
| 跨平台桥接 | `ai-skill-link` + `Skiller` | 软链接方式最轻量 |
| 技能管理 | `npx skills`(`npx skills@latest add your-workflow-suite`) | 已形成生态 |
| 记忆层 | Acontext 或自建 | 开源可定制 |
| 自我迭代 | EvoSkills + task-observer | 验证器驱动,质量可控 |
| 插件市场 | Claude 官方市场 + 自建市场 | 官方+自建双通道 |

## 开发约定

以下约定部分来自项目构思文档,部分是本仓库现有规范;尚无代码,故无语言/框架层面的强制约束:

- **文档与注释语言**:中文(项目文档 `docs/基本构思.md` 为中文,遵循此惯例)
- **技能封装**:所有技能以 `SKILL.md` 形式封装,遵循 Anthropic Agent Skills 标准格式
- **仓库结构**:已按 `skills/`、`hooks/`、`adapters/` 组织(Phase 1 落地);新增技能复制 `skills/_template/`
- **代码风格**:遵循"小、可组合、随时可改"的设计哲学,避免过度设计;Python 适配层在 `adapters/zcode/`
- **修改前先 Read**:本仓库文件极少,任何修改前先读取目标文件
- **开发偏好与默认配置**:见 `docs/开发偏好与默认配置.md`(经问答确认后归档,含记忆层路线、技术栈、本地小模型默认配置、待定项等)
- **不要臆造**:项目尚无实现,涉及"现状"的描述必须以 `docs/基本构思.md` 为准,不要假设已有功能或配置

## 构建 / 测试 / 部署

- **安装 zcode CLI**:`python3 -m venv .venv && .venv/bin/pip install -e ./adapters`(PEP 668 环境必须用 venv)
- **CLI 验证命令**:`.venv/bin/zcode skills list`、`.venv/bin/zcode --profile local-qwen3.6-35b info`、`.venv/bin/zcode platforms list`、`.venv/bin/zcode workflow list`、`.venv/bin/zcode workflow run feature-dev --dry-run`、`.venv/bin/zcode version`(版本)、`.venv/bin/zcode update --dry-run`(自更新预览)、`.venv/bin/zcode ticket context`(接手先看)、`.venv/bin/zcode ticket validate`(提交前校验)、`.venv/bin/zcode git status`(git 管理，TTY 进 TUI)、`.venv/bin/zcode release --dry-run`(版本迭代预览)
- **跨平台安装**:`bash scripts/install.sh`(全局,主目标 `~/.agents/skills`);`--project <dir>` 项目级;`--uninstall` 卸载;Windows 用 `powershell -ExecutionPolicy Bypass -File ./scripts/install.ps1`(装技能 + `zcode.cmd` 全局命令,自动加用户 PATH)
- **npm 分发**:`npm link` 后 `zcode` 可用(需先安装 Python 包)
- **测试命令**:`python3 -m unittest discover -s adapters/tests`(unittest 零依赖);技能质量评估用 `zcode market validate`(Phase 4)
- **部署流程**:Layer 0 交付物已就绪(`install.sh` + 8 平台 `INSTALL.md`);各平台深度插件(`plugin.json`)与技能市场发布待后续

## 给 AI 代理的操作指引

1. 首次进入项目:先读 `docs/基本构思.md`(唯一需求来源),再读本文件
2. 当前阶段开发工作,主要是在**推进 Phase 4 剩余项**(EvoSkills 自我迭代、各平台深度插件、技能市场)或**打磨已落地能力**;参考 `docs/基本构思.md` 第五节(本地小模型优化定稿)与 `docs/开发偏好与默认配置.md` 确定方向
3. 如需修改 `docs/基本构思.md`,注意它是需求源头,改动需谨慎并与用户确认
4. 本文件(AGENTS.md)需与项目实际状态保持同步:Phase 1 已落地(目录结构、脚本、配置文件已创建),后续进展请继续更新本文件的"当前状态"、"构建/测试/部署"等章节

## 工单工作台协议（本仓库已启用）

本仓库已启用工单驱动工作台（Layer 2，`zcode ticket`）：双状态机 + 可执行强制。任何 Agent 在本仓库干活时：

1. **接手先看**：`zcode ticket context`（或读 `STATUS.md`），一屏拿全貌，细节按需再读。
2. **状态推进一律走命令**，绝不手动改锚点行（`Phase:` / `Status:` / `Current Ticket:` / `Domain:` / `Resolution:` / `TestCommand:` / `BranchMode:`）。
3. 干活前 `zcode ticket begin T-XXX`；修复类工单 close 前必须 `zcode ticket resolve T-XXX "根因+修复+验证"`；`zcode ticket validate` 通过后才提交。
4. pre-commit hook 会拦截：Phase 未到 verify/review/commit、当前工单 in-progress、STATUS.md 过期、Domain 已填但术语表为空、TestCommand 运行失败（测试门禁，`git config zcode.test-gate false` 可关）。
5. **close 自动收尾**（无需人工）：`CHANGELOG.md` 缺本工单号时自动从 Resolution 补录（版本自动 bump；文件不存在自动创建 `[0.1.0]` 基线）；`tickets.md` / `STATUS.md` / `docs/CONTEXT.md` / 术语表 / `.vibe/` / `CHANGELOG.md` 自动提交（`T-XXX 状态收尾`），工作区保持干净——不再需要"状态收尾/补记录"类工单。
6. **人工同步**（随工单一起提交）：`README.md` / `AGENTS.md` / **术语表（本次引入的新术语 `gloss add`——写入靠命令、登记靠核对，validate 只拦空表与格式，漏登记不会自动发现）** / 技能清单（ask-zcode / skills/README / marketplace.json）按本次变更同步——**不允许关单后文档未更新**。
7. 新术语立即 `zcode ticket gloss add <术语> <定义>` 记入 `docs/UBIQUITOUS_LANGUAGE.md`。
8. 当前工单在 `tickets.md`；`zcode ticket next` 看可拾取项。

### 三系统分工（workbench × handoff × mem0）

| 系统 | 管什么 | 接手路径 |
|---|---|---|
| workbench（`zcode ticket`） | 项目级状态源：工单/阶段/验证证据/术语表（单一事实来源） | `zcode ticket context` |
| handoff（`zcode handoff`） | 会话级接力：目标/下一步；工作台项目"进行中"自动引用工单状态（缺省自动、传参覆盖） | 会话开始 `load` / 结束 `save` |
| mem0（`zcode memory`） | 跨会话语义记忆：自由事实/偏好/经验检索（与术语表互补：术语表=规范词条强制，mem0=自由事实） | `zcode memory search <查询>` |
