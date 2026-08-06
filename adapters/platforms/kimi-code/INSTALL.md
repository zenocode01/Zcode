# Kimi Code 适配说明

## 技能目录

- 用户级：`$KIMI_CODE_HOME/skills/`（默认 `~/.kimi-code/skills/`）+ `~/.agents/skills/`
- 项目级：`.kimi-code/skills/` + `.agents/skills/`（项目根 = 向上找最近含 `.git` 的目录）
- 优先级：Project > User > Extra > Builtin

## 安装方式

```bash
bash scripts/install.sh            # ~/.agents/skills 全局生效（Kimi Code 原生支持）
# 或手动:
mkdir -p ~/.kimi-code/skills
ln -s <repo>/skills/tdd ~/.kimi-code/skills/tdd
```

## 配置要点（~/.kimi-code/config.toml）

```toml
# 额外技能目录（团队技能等）
extra_skill_dirs = ["~/team-skills"]
```

## 注意事项

- 数据根 `~/.kimi-code/` 可用环境变量 `KIMI_CODE_HOME` 迁移。
- 支持目录形式 `<name>/SKILL.md` 和扁平 `<name>.md`（同名时目录优先）。
- 读取上下文：项目级 `AGENTS.md` / `.kimi-code/AGENTS.md`、全局 `~/.agents/AGENTS.md`、`$KIMI_CODE_HOME/AGENTS.md`。
