# Zcode — AI 技能的"操作系统"

一套**轻量、可插拔**的"技能运行时环境"：将 AI 技能从"一次性指令"升级为**可安装、可组合、可记忆、可进化**的能力产品。只需维护一个技能仓库，就能在任意 AI 工具（Claude Code、Cursor、Codex、Gemini CLI 等）中获得一致的工作流能力，且针对本地部署的小模型做了专门优化。

## 快速开始

```bash
# 1. 安装 Python 适配层（PEP 668 环境必须用 venv）
python3 -m venv .venv && .venv/bin/pip install -e ./adapters

# 2. 跨平台安装技能（全局，软链到 ~/.agents/skills 等；--project <dir> 项目级）
bash scripts/install.sh

# 3. 常用命令（npm link 后可直接用全局 zcode）
.venv/bin/zcode skills list                      # 技能清单
.venv/bin/zcode --profile local-qwen3.6-35b info # 本地小模型 profile
.venv/bin/zcode platforms list                   # 8 平台支持
.venv/bin/zcode tools list                       # 工具映射表（spawn/parallel/todo/review → 8 平台）
.venv/bin/zcode workflow list                    # 工作流模板
.venv/bin/zcode workflow run feature-dev --dry-run
.venv/bin/zcode memory add/search/list           # 记忆层（mem0 + Qdrant 本地）
.venv/bin/zcode handoff save/load                # 会话接力
.venv/bin/zcode skill log/audit <技能名>          # EvoSkills 自我迭代
.venv/bin/zcode market list/validate             # 技能市场与质量校验
.venv/bin/zcode ticket init <project>            # 工单驱动工作台（双状态机 + 可执行强制）
.venv/bin/zcode ticket context                   # 接手仓库先看状态（一屏摘要，省 token）
```

> 本项目自身也启用了工单工作台：接手先 `zcode ticket context`（或读 `STATUS.md`），状态推进一律走命令，提交由 pre-commit hook 强制校验。

## 目录结构

```
├── skills/           # 核心技能库（Layer 1），双版本：SKILL.md（云）/ SKILL.local.md（本地）
│                     # 12 个技能 + _template 模板：
│                     # ask-zcode / brainstorming / code-review / diagnose / evoskills /
│                     # grill-me / handoff / improve-arch / subagent-driven-development /
│                     # tdd / workbench / writing-plans
│                     # 每个技能下 .memory/：experience.log / improvements.md / context-snapshot.json
├── workflows/        # 确定性工作流模板（Layer 2）：feature-dev / ticket-dev + 引擎（skill/prompt/command/subagent 步骤）
├── metaskills/       # MetaSkill 自由编排（Layer 2）：模型生成计划 + 复用执行器
├── tickets.md        # 工单列表（Status/Depends/Resolution 锚点，zcode ticket 管理）
├── STATUS.md         # 单屏总览（zcode ticket 状态命令自动刷新）
├── .vibe/            # 工作台内部状态（log.md / evidence / hooks / vibe.meta）
├── adapters/         # 跨平台适配层（Layer 0）：zcode 包（profile/Provider/工具三层降级/MemStore/CLI/工具映射表/ticket）
│   ├── platforms/    # 8 平台 INSTALL.md
│   └── tests/        # 单元测试（unittest 零依赖，python3 -m unittest discover -s adapters/tests）
├── hooks/            # git 安全守卫钩子
├── scripts/          # install.sh 跨平台一键安装脚本
├── docs/             # 需求与设计（基本构思 / 开发偏好 / CONTEXT 状态中枢 / UBIQUITOUS_LANGUAGE 术语表 / ADR）
├── bin/              # npm CLI 分发入口（package.json）
├── marketplace.json  # 技能市场清单（market validate 质量校验）
└── .claude-plugin/   # Claude Code 深度插件（plugin.json）
```

## 平台支持

| 平台 | 技能目录（原生） | 兼容目录 | 安装方式 |
|------|-----------------|---------|---------|
| Claude Code | `~/.claude/skills/` | `~/.agents/skills/` | install.sh |
| Cursor | `~/.cursor/skills/` | `~/.agents/skills/` | install.sh |
| Codex | `~/.codex/skills/` | `~/.agents/skills/` | install.sh |
| Gemini CLI | `~/.gemini/skills/` | `.agents/skills/` | install.sh / `gemini skills link` |
| opencode | `~/.config/opencode/skills/` | `~/.claude/skills/`、`~/.agents/skills/` | install.sh |
| Kimi Code | `~/.kimi-code/skills/` | `~/.agents/skills/` | install.sh |
| Pi | `~/.pi/agent/skills/` | `~/.agents/skills/` | install.sh |
| Reasonix | `~/.reasonix/skills/` | `.agents/skills/`、`.claude/skills/` | install.sh |

> `~/.agents/skills/` 是跨工具事实标准目录（opencode / Kimi Code / Pi / Cursor / Reasonix 原生支持），install.sh 以它为主安装目标，平台原生目录做双保险。
> 深度插件：Claude Code（`.claude-plugin/plugin.json`）、opencode（permission.skill）、Kimi Code（installed.json）。

## 当前状态

Phase 1/2/3 核心能力全部落地 + Phase 4 起步（2025-08）：

- **技能库（Layer 1）**：12 个技能双版本（`SKILL.md` 云 / `SKILL.local.md` 本地小模型）+ `_template/` 模板（含 `.memory/` 技能级记忆）
- **适配层（Layer 0）**：Python 包 `zcode`（profile / Provider / 工具三层降级 / MemStore / CLI / 工具映射表）、8 平台 `INSTALL.md`、`scripts/install.sh` 一键安装、npm 分发入口
- **工作流与编排（Layer 2）**：确定性工作流模板 `feature-dev` / `ticket-dev` + 引擎；MetaSkill 自由编排（模型生成计划 + 复用执行器）；子代理驱动开发（独立上下文 / ledger / 逐任务审查）
- **工单驱动工作台（Layer 2，移植 vibe-workbench）**：`zcode ticket` 命令族（init/add/begin/phase/transition/close/resolve/context/gloss/status/validate/next/log/install/projects/switch/ask）——双状态机（Agent 阶段机 + 工单生命周期机）+ 可执行强制（守卫 / 依赖环检测 / 验证证据 / STATUS 自刷新 / pre-commit 闸门 / 自动分支）+ `skills/workbench` 技能；与 vibe-workbench 文件格式与注册表兼容，两 CLI 可混用
- **记忆与迭代（Layer 3）**：`zcode memory`（mem0 + Qwen3-Embedding-8B + Qdrant 本地，BM25/实体增强已启用）；会话接力 `zcode handoff`；EvoSkills 自我迭代 `zcode skill log/audit`（阈值 70% / 2 条）
- **生态（Phase 4 起步）**：技能市场 `zcode market list/validate/generate`（marketplace.json 质量校验）+ Claude Code 深度插件
- **测试**：`adapters/tests/`（unittest 零依赖，`python3 -m unittest discover -s adapters/tests`）

尚未实现：技能市场远程分发与社区贡献、其余平台深度插件、技能市场发布。路线图见 `docs/基本构思.md`。

## 设计参考

- `docs/基本构思.md` — 四层架构 + 本地小模型优化定稿（唯一需求来源）
- `docs/开发偏好与默认配置.md` — 已确认的开发偏好与默认配置
- `CHANGELOG.md` — 变更记录（0.1.0 四层落地 / 0.1.1 打磨迭代 / 0.2.0 工单工作台 / 0.2.1 测试防线）
- `mem0/` — mem0 源码，仅作记忆层学习参考，不提交 git
