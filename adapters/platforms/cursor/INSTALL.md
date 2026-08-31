# Cursor 适配说明

## 技能目录

- 项目级：`.cursor/skills/`、`.agents/skills/`
- 用户级：`~/.cursor/skills/`、`~/.agents/skills/`
- 兼容目录：`.claude/skills/`、`.codex/skills/`、`~/.claude/skills/`、`~/.codex/skills/`

## 安装方式

```bash
bash scripts/install.sh --project <你的项目>   # 项目级 .agents/skills
# 或全局:
bash scripts/install.sh                        # ~/.agents/skills 生效
```

## 注意事项

- 项目级 `.agents/skills/` 同时覆盖 Cursor、opencode、Kimi Code、Pi、Gemini、Reasonix，推荐优先使用。
- 技能格式遵循 Agent Skills 标准（`SKILL.md` + frontmatter）。
