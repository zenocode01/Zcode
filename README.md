# Zcode — AI 技能的"操作系统"

一套**轻量、可插拔**的"技能运行时环境"：将 AI 技能从"一次性指令"升级为**可安装、可组合、可记忆、可进化**的能力产品。只需维护一个技能仓库，就能在任意 AI 工具中获得一致的工作流能力，且针对本地部署的小模型做了专门优化。

## 快速开始

```bash
# 1. 安装 Python 适配层
cd adapters && pip install -e . && cd ..

# 2. 跨平台安装技能（全局，软链到 ~/.agents/skills 等）
bash scripts/install.sh

# 3. 查看技能 / profile / 平台支持
zcode skills list
zcode --profile local-qwen3.6-27b info
zcode platforms list
```

## 目录结构

```
├── skills/        # 核心技能库（Layer 1），双版本：SKILL.md（云）/ SKILL.local.md（本地）
├── adapters/      # 跨平台适配层（Layer 0）：profile、LLM Provider、8 平台适配文档
│   └── platforms/ # 各平台 INSTALL.md
├── hooks/         # 钩子（git 安全守卫等）
├── scripts/       # install.sh 跨平台一键安装脚本
├── docs/          # 需求与设计文档（基本构思 / 开发偏好 / 本地小模型优化草案）
└── bin/           # npm CLI 分发入口
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

## 当前状态

Phase 1 骨架已落地（2025-08）：仓库结构、适配层基座（profile + OpenAI 兼容 Provider）、8 平台安装脚本、tdd 示例技能。技能批量移植、记忆层（mem0）、编排引擎见 `docs/基本构思.md` 路线图。

## 设计参考

- `docs/基本构思.md` — 四层架构与实施路线图（唯一需求来源）
- `docs/开发偏好与默认配置.md` — 已确认的开发偏好与默认配置
- `docs/本地小模型优化-设计草案.md` — 面向 Qwen3.6-27B（llama.cpp / 256K）的优化设计
- `mem0/` — mem0 源码，仅作记忆层学习参考，不提交 git
