# Pi（pi-agent）适配说明

## 技能目录

- 全局：`~/.pi/agent/skills/`、`~/.agents/skills/`
- 项目级：`.pi/skills/`、`.agents/skills/`（从 cwd 沿父目录向上）

## 安装方式

```bash
bash scripts/install.sh            # ~/.agents/skills 全局生效（Pi 原生支持）
# 或手动:
mkdir -p ~/.pi/agent/skills
ln -s <repo>/skills/tdd ~/.pi/agent/skills/tdd
```

## 注意事项

- 加载方式：`/skill:<name>` 手动调用，或模型自动加载；格式遵循 Agent Skills 标准（agentskills.io）。
- 上下文文件：读取 `AGENTS.md`（或 `CLAUDE.md`，`AGENTS.override.md` 可覆盖），来源含 `~/.pi/agent/AGENTS.md`、父目录逐级、当前目录。
- 系统提示：`.pi/SYSTEM.md` / `~/.pi/agent/SYSTEM.md`。
- 扩展机制：TypeScript Extensions 与 Pi Packages（npm/git），也可通过 pi package 分发技能。
