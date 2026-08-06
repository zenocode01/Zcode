# AGENTS.md — Zcode 项目指南

本文件供 AI 编码代理阅读。阅读者应对项目一无所知,请先完整阅读本文件,再进入项目操作。

## 项目概述

**Zcode**(仓库路径:`ZENO/Zcode/Zcode-0.0`)的目标是构建一个 **AI 技能的"操作系统"**——一套轻量的、可插拔的"技能运行时环境",而非另一个重型框架。核心理念:将 AI 技能从"一次性指令"升级为"可安装、可组合、可记忆、可进化"的能力产品。

设计哲学借鉴两个开源项目:
- **Matt Pocock 的技能集**:"小、可组合、随时可改",每个技能是独立的 Markdown 指令集,像乐高积木
- **Superpowers**:"强制工作流",通过启动时注入引导上下文,让 Agent 先查技能再行动

最终效果:只需维护一个技能仓库,就能在任意 AI 工具(Claude Code、Cursor、Codex、Gemini CLI 等)中获得一致的工作流能力,且能力随使用不断进化和记忆。

## 当前状态(重要)

> **Phase 1 完整落地 + Phase 2 起步(2025-08):技能库、适配层、8 平台安装、确定性工作流模板、工具三层降级。**

- 需求与设计文档:
  - `docs/基本构思.md` —— 唯一权威需求来源(四层架构 + 实施路线图),开发前务必先读
  - `docs/开发偏好与默认配置.md` —— 已确认的开发偏好与默认配置(记忆路线/技术栈/目标模型)
  - `docs/本地小模型优化-设计草案.md` —— 面向 Qwen3.6-27B(llama.cpp / 256K)的本地优化设计
- 已落地:
  - `skills/` —— 技能库,双版本(`SKILL.md` 云 / `SKILL.local.md` 本地),7 个核心技能(grill-me/brainstorming/writing-plans/tdd/diagnose/code-review/improve-arch) + `_template/` 模板
  - `adapters/` —— Python 包 `zcode`(profile 加载、OpenAI 兼容 Provider、工具三层降级、CLI)、`profiles/local-qwen3.6-27b.yaml`、8 平台 `platforms/*/INSTALL.md`
  - `workflows/` —— 确定性工作流模板(Layer 2 起步):`feature-dev` 示例 + 引擎 `zcode/workflow.py`
  - `scripts/install.sh` —— 跨平台一键安装(主目标 `~/.agents/skills` + 8 平台原生目录双保险)
  - `hooks/` —— git 安全守卫示例;`bin/zcode.js` + `package.json` —— npm 分发入口
- Git 仓库已有提交(`main` 分支);无远程仓库
- 尚未实现:Layer 2 编排增强(MetaSkill/子代理编排)、Layer 3 记忆层(mem0,Phase 3)、各平台深度插件、Embedding 选型

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
- **CLI 验证命令**:`.venv/bin/zcode skills list`、`.venv/bin/zcode --profile local-qwen3.6-27b info`、`.venv/bin/zcode platforms list`、`.venv/bin/zcode workflow list`、`.venv/bin/zcode workflow run feature-dev --dry-run`
- **跨平台安装**:`bash scripts/install.sh`(全局,主目标 `~/.agents/skills`);`--project <dir>` 项目级;`--uninstall` 卸载
- **npm 分发**:`npm link` 后 `zcode` 可用(需先安装 Python 包)
- **测试命令**:暂无测试框架;技能质量评估体系待建立(Phase 4)
- **部署流程**:Layer 0 交付物已就绪(`install.sh` + 8 平台 `INSTALL.md`);各平台深度插件(`plugin.json`)与技能市场发布待后续

## 给 AI 代理的操作指引

1. 首次进入项目:先读 `docs/基本构思.md`(唯一需求来源),再读本文件
2. 当前阶段开发工作,主要是在**推进 Phase 2 剩余部分**(MetaSkill 自由编排、子代理编排)或**启动 Phase 3**(记忆层 mem0);参考 `docs/开发偏好与默认配置.md` 与 `docs/本地小模型优化-设计草案.md` 确定方向
3. 如需修改 `docs/基本构思.md`,注意它是需求源头,改动需谨慎并与用户确认
4. 本文件(AGENTS.md)需与项目实际状态保持同步:Phase 1 已落地(目录结构、脚本、配置文件已创建),后续进展请继续更新本文件的"当前状态"、"构建/测试/部署"等章节
