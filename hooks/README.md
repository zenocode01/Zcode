# hooks/ — 钩子

Zcode 通过钩子在"技能安装/使用/提交"等环节挂接安全检查与工作流约束，类似 Superpowers 的"强制工作流"机制。

## 当前内容

| 钩子 | 作用 | 安装方式 |
|------|------|---------|
| `git-guard/pre-commit.sh` | git 危险命令守卫（示例）：提交内容含危险 git 命令模式时阻止提交 | 手动复制到目标仓库 `.git/hooks/` |

## 使用说明

```bash
# 安装到某仓库（示例）
cp hooks/git-guard/pre-commit.sh <repo>/.git/hooks/pre-commit
chmod +x <repo>/.git/hooks/pre-commit
```

## 说明

- `pre-commit` 无法拦截 `push` 等远程操作——真正的 push 拦截需要 `pre-push` 钩子，后续补充。
- 完整方案可参考技能 `git-guardrails-claude-code`（Claude Code hooks，阻止 push / reset --hard / clean 等危险命令）。
- 后续 Phase 2 将在此扩展"启动引导钩子"：Agent 启动时先查技能索引再行动。
