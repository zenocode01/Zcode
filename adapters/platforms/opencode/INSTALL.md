# opencode 适配说明

## 技能目录

- 项目级：`.opencode/skills/<name>/SKILL.md`
- 全局：`~/.config/opencode/skills/<name>/SKILL.md`
- 兼容目录：`.claude/skills/`、`~/.claude/skills/`、`.agents/skills/`、`~/.agents/skills/`（项目级从 cwd 沿目录树向上直到 git worktree 根）

## 安装方式

```bash
bash scripts/install.sh            # ~/.agents/skills 全局生效（opencode 原生支持）
# 或手动:
mkdir -p ~/.config/opencode/skills
ln -s <repo>/skills/tdd ~/.config/opencode/skills/tdd
```

## 配置要点（opencode.json）

```json
{
  "permission": {
    "skill": {
      "allow": ["tdd"],
      "deny": ["untrusted-skill"]
    }
  }
}
```

- 全局 `~/.config/opencode/opencode.json` + 项目 `opencode.json`
- `permission.skill` 按模式控制技能权限（allow / deny / ask）

## 注意事项

- **name 约束**：技能名必须匹配 `^[a-z0-9]+(-[a-z0-9]+)*$` 且与目录名一致（本项目 skills/ 规范已遵守）。
- 插件机制：`.opencode/plugins/`、`~/.config/opencode/plugins/` 或 npm 包（技能本体走目录扫描）。
