# workflows/ — 确定性工作流模板（Layer 2）

本地小模型模式下，**不依赖模型自由编排**（MetaSkill 对 14B-32B 太吃力），改为**确定性线性工作流**：显式步骤 + 条件分支，由外部 runner 顺序执行，模型只做"当前步该做什么"的决策。

## 工作流文件格式（YAML）

```yaml
name: <工作流名>            # 须匹配 ^[a-z0-9]+(-[a-z0-9]+)*$
description: <一句话说明>
steps:
  - skill: <技能名>          # 加载 skills/<name>/SKILL.local.md 作为指令（按 profile 选版本）
  - prompt: <直接给模型的提示词>
  - command: <shell 命令>    # 外部执行（如跑测试）
    when: <条件>             # 可选：显式条件分支（true/false 或简单表达式）
```

- 步骤按顺序执行；`skill` 步骤注入对应技能文件内容，`command` 步骤由 runner 直接执行，`prompt` 步骤原样给模型。
- 条件分支用 `when`，值可为 `true`/`false` 或 `${...}` 占位（由调用方提供变量）。
- 工作流文件放本目录，一个文件一个工作流。

## 当前工作流

| 工作流 | 说明 |
|--------|------|
| `feature-dev.yaml` | 功能开发：需求拷问 → 设计 → 计划 → TDD 实现 → 审查 |

## CLI 用法

```bash
zcode workflow list                 # 列出工作流
zcode workflow run feature-dev      # 执行（需本地端点）
zcode workflow run feature-dev --dry-run   # 只打印步骤计划
```
