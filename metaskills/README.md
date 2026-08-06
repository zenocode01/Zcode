# metaskills/ — MetaSkill 自由编排（Layer 2）

**MetaSkill（元技能）**：不写固定流程，把**可用技能 + 编排规则**告诉模型，由模型自己生成步骤计划（model-orchestrated）。

与 `workflows/`（确定性模板）的关系：

| 模式 | 编排者 | 适用模型 | profile 字段 |
|------|--------|---------|-------------|
| 确定性模板（workflows/） | 外部 runner | 本地小模型（默认） | `orchestration: deterministic` |
| MetaSkill 自由编排（metaskills/） | 模型自己 | 云端/强模型 | `orchestration: meta` |

> 本地小模型默认走确定性模板（草案 §3.4）；MetaSkill 是强模型的可选增强，可用 `zcode metaskill run <name> --force-meta` 强制试用。

## MetaSkill 文件格式（YAML）

```yaml
name: <元技能名>            # 须匹配 ^[a-z0-9]+(-[a-z0-9]+)*$
description: <一句话说明>
when: <触发场景描述>
skills:                     # 可编排的技能清单（name 必须存在于 skills/）
  - grill-me
  - brainstorming
rules:                      # 编排规则（硬约束，逐字给模型）
  - "brainstorming 获批准前不得进入实现类技能"
  - "如有疑问，先问用户再继续"
```

模型编排输出的计划格式（引擎解析）：

```
1. skill: <技能名>
2. prompt: <说明>
```

## 当前 MetaSkill

| 元技能 | 说明 |
|--------|------|
| `feature-dev` | 功能开发：让模型在 5 个技能间自由编排流程 |

## CLI 用法

```bash
zcode metaskill list                      # 列出 MetaSkill
zcode metaskill run feature-dev --dry-run # 只生成编排计划，不执行
zcode metaskill run feature-dev           # 生成计划并执行（需本地端点）
```
