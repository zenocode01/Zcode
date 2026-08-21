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

## 深度插件（三合一）

Zcode 提供 pi-agent 深度插件（`adapters/platforms/pi/extension/`），通过根 `package.json` 的 `pi` 键打包为 Pi Package：

| 能力 | 用法 |
|------|------|
| 命令透传（人用） | `/zcode <子命令>`，如 `/zcode skills list`、`/zcode ticket context` |
| 只读工具（AI 用） | `zcode_ticket_context` / `zcode_memory_search` / `zcode_skills_list` / `zcode_glossary`，模型可主动调用 |
| 打包分发 | `pi install` 一键装齐 skills + extension |

### 安装

```bash
# 前置：先装 zcode CLI（供 extension 调用）
bash scripts/install.sh

# 方式一：本地路径安装
pi install /home/zeno/ZENO/Zcode/Zcode-0.0

# 方式二：git 源安装
pi install git:github.com/zenocode01/Zcode.git

# 方式三：仅当前会话试跑（不安装）
pi -e adapters/platforms/pi/extension/index.ts
```

### 卸载

```bash
pi remove /home/zeno/ZENO/Zcode/Zcode-0.0   # 或对应的 npm/git 源
```

### 注意

- extension 调用的 zcode CLI 需已在 PATH（或 `~/.local/bin/zcode` / `python3 -m zcode`）；未安装时 `/zcode` 会提示装法，不影响 pi 启动。
- 只读工具无副作用；有副作用写操作（`ticket begin/close`、git 写、`memory add`）仅经 `/zcode` 命令由人显式触发。
- extension 从可信来源安装（见 pi 安全说明），运行需项目信任。
