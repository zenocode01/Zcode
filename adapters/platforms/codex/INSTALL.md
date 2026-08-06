# Codex（OpenAI CLI）适配说明

## 技能目录

- 用户级：`~/.codex/skills/<name>/SKILL.md`
- 项目级：`.codex/skills/<name>/SKILL.md`

## 安装方式

```bash
bash scripts/install.sh            # 检测到 ~/.codex/skills 存在时自动补软链
# 或手动:
mkdir -p ~/.codex/skills
ln -s <repo>/skills/tdd ~/.codex/skills/tdd
```

## 注意事项

- 兼容：Cursor 也会读取 `~/.codex/skills/` 与 `.codex/skills/`。
- 技能格式遵循 Agent Skills 标准。
