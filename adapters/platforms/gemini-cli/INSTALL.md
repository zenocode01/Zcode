# Gemini CLI 适配说明

## 技能目录

- 项目级：`.gemini/skills/<name>/SKILL.md`（也可用 `.agents/skills/` 别名，workspace 需 trusted）
- 用户级：`~/.gemini/skills/<name>/SKILL.md`

## 安装方式

```bash
# 方式一：官方 link 命令（正适合软链）
gemini skills link <repo>/skills/tdd

# 方式二：install.sh 项目级
bash scripts/install.sh --project <你的项目>
```

## 注意事项

- Gemini 允许 `skills/SKILL.md` 扁平形式，但推荐统一使用 `<name>/SKILL.md` 一层深结构。
- 项目级 `.agents/skills/` 需在 workspace 设置 trusted 才会生效。
