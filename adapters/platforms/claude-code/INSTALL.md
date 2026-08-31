# Claude Code 适配说明

## 技能目录

- 用户级：`~/.claude/skills/<name>/SKILL.md`
- 项目级：`.claude/skills/<name>/SKILL.md`

## 安装方式

```bash
bash scripts/install.sh            # 检测到 ~/.claude/skills 存在时自动补软链
# 或手动:
mkdir -p ~/.claude/skills
ln -s <repo>/skills/tdd ~/.claude/skills/tdd
```

## 注意事项

- **只扫一层深**：每个技能目录必须直接放在 `skills/` 下，不支持嵌套。
- 兼容：opencode、Cursor、Reasonix 也会读取 `~/.claude/skills/`，装一次多处生效。
- 参考技能 `git-guardrails-claude-code` 可在 Claude Code 中配置 hooks 拦截危险 git 命令。
