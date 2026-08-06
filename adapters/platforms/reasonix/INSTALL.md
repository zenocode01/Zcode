# Reasonix（resonix）适配说明

## 技能目录

- 全局：`~/.reasonix/skills/`（Windows 为 `%APPDATA%\reasonix\skills`；`REASONIX_HOME` 可覆盖）
- 项目级：`.reasonix/skills/`
- 兼容目录：`.agents/skills/`、`.agent/skills/`、`.claude/skills/`（项目根和 home 下都扫，含 `~/.agents/skills/`、`~/.agent/skills/`、`~/.claude/skills/`；Claude 根目录里的扁平 `<name>.md` 也兼容加载）

## 安装方式

```bash
bash scripts/install.sh            # ~/.agents/skills 全局生效（Reasonix 原生支持）
# 或手动:
mkdir -p ~/.reasonix/skills
ln -s <repo>/skills/tdd ~/.reasonix/skills/tdd
```

## 配置要点（reasonix.toml）

```toml
# 自定义技能根目录
SkillCustomPaths = ["/path/to/team-skills"]
```

- 全局配置：`~/.reasonix/config.toml`；项目配置：`reasonix.toml`；凭证：`~/.reasonix/.env`
- 插件/扩展：见 `docs/EXTENSIONS.md`；hooks：`~/.reasonix/settings.json`

## 注意事项

- 技能名沿用本项目规范（`^[a-z0-9]+(-[a-z0-9]+)*$`）即可被各兼容目录正确加载。
