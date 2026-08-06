# platforms/ — 8 平台适配文档（Layer 0 交付物）

每平台一份 `INSTALL.md`：技能目录路径、配置要点、安装方式与注意事项。

## 平台支持总表

| 平台 | 原生技能目录 | 兼容目录 | 配置文件 | 来源 |
|------|-------------|---------|---------|------|
| Claude Code | `~/.claude/skills/`、`.claude/skills/` | — | — | [官方文档](https://code.claude.com/docs/en/skills) |
| Cursor | `~/.cursor/skills/`、`.cursor/skills/` | `~/.claude/skills/`、`~/.codex/skills/`、`~/.agents/skills/` 等 | `~/.cursor/` | [docs](https://cursor.com/docs/skills) |
| Codex | `~/.codex/skills/`、`.codex/skills/` | — | `~/.codex/` | 交叉确认 |
| Gemini CLI | `~/.gemini/skills/`、`.gemini/skills/` | `.agents/skills/`（需 trusted） | `~/.gemini/` | [官方教程](https://developers.googleblog.com/en/gemini-cli/) |
| opencode | `~/.config/opencode/skills/`、`.opencode/skills/` | `~/.claude/skills/`、`~/.agents/skills/` | `opencode.json` | [docs](https://opencode.ai/docs/skills/) |
| Kimi Code | `~/.kimi-code/skills/`、`.kimi-code/skills/` | `~/.agents/skills/` | `config.toml` | [docs](https://github.com/MoonshotAI/kimi-code) |
| Pi | `~/.pi/agent/skills/`、`.pi/skills/` | `~/.agents/skills/` | `~/.pi/agent/AGENTS.md` | [pi.dev](https://github.com/badlogic/pi-mono) |
| Reasonix | `~/.reasonix/skills/`、`.reasonix/skills/` | `.agents/skills/`、`.agent/skills/`、`.claude/skills/` | `reasonix.toml` | [reasonix](https://github.com/esengine/DeepSeek-Reasonix) |

> **关键洞察**：`~/.agents/skills/` 是跨工具事实标准——opencode、Kimi Code、Pi、Cursor、Reasonix 全部原生支持，因此 install.sh 以它为主安装目标。

## 通用安装方式

```bash
# 全局安装（主目标 ~/.agents/skills + 已存在的平台原生目录）
bash scripts/install.sh

# 强制创建全部平台原生目录（双保险）
bash scripts/install.sh --all-platforms

# 项目级安装
bash scripts/install.sh --project <dir>
```

## 软链注意事项

1. **1 层深约束**：所有工具只支持 `skills/<name>/SKILL.md` 一层，install.sh 逐个技能建软链，**不能**把整个技能仓库链成一个大目录。
2. **命名约束**：`SKILL.md` 全大写、frontmatter 含 `name` + `description`；opencode 要求 name 匹配 `^[a-z0-9]+(-[a-z0-9]+)*$` 且与目录名一致。
3. **重名冲突**：目标目录已有同名技能且非本仓库软链时，install.sh 跳过并提示。
