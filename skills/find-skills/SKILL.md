---
name: find-skills
description: 技能发现与安装——当用户问"怎么做 X"、"找 X 技能"、"有 X 的技能吗"、"能扩展能力吗"、或表达想要某类帮助时，帮你在 open agent skills 生态中搜索、验证并安装合适的技能。
---

# find-skills — 技能发现与安装

> 帮助用户从 [skills.sh](https://skills.sh/) 开放生态中发现、验证并安装合适的技能。当用户寻找可能以现有技能满足的需求时使用本技能。

## 何时使用

- 用户问"怎么做 X"，而 X 可能是已有技能覆盖的常见任务
- 用户说"找 X 技能"或"有 X 的技能吗"
- 用户问"你能做 X 吗"，而 X 是某种专业能力
- 用户表达扩展 Agent 能力的兴趣
- 用户想搜索工具、模板或工作流
- 用户提到希望获得某领域（设计、测试、部署等）的帮助

## 什么是 Skills CLI？

Skills CLI（`npx skills`）是开放 Agent 技能生态的包管理器。技能是模块化包，用专业知识、工作流和工具扩展 Agent 能力。

**核心命令：**

- `npx skills find [query] [--owner <owner>]` — 交互式或按关键词搜索技能，可选限定 GitHub owner
- `npx skills add <package>` — 从 GitHub 或其他来源安装技能
- `npx skills update` — 更新所有已安装技能

**浏览技能：** https://skills.sh/

## 工作流程

### 第一步：理解需求

识别：
1. 领域（如 React、测试、设计、部署）
2. 具体任务（如写测试、创建动画、审查 PR）
3. 是否是常见到可能有现成技能的任务

### 第二步：先看排行榜

在跑 CLI 搜索前，先查看 [skills.sh 排行榜](https://skills.sh/) 看是否已有该领域的知名技能。排行榜按总安装量排序，展示最流行和经过验证的选项。

例如 Web 开发方向的热门技能：
- `vercel-labs/agent-skills` — React、Next.js、Web 设计（100K+ 安装）
- `anthropics/skills` — 前端设计、文档处理（100K+ 安装）

### 第三步：搜索技能

如果排行榜没有覆盖用户需求，运行 find 命令：

```bash
npx skills find [query] [--owner <owner>]
```

例如：

- 用户问"怎么让 React 应用更快？" → `npx skills find react performance`
- 用户问"能帮我做 PR 审查吗？" → `npx skills find pr review`
- 用户问"我需要创建 changelog" → `npx skills find changelog`

### 第四步：验证质量（安装前必做）

**不要仅凭搜索结果推荐技能。** 必须验证：

1. **安装量** — 优先推荐 1K+ 安装的技能，低于 100 的谨慎对待
2. **来源声誉** — 官方来源（`vercel-labs`、`anthropics`、`microsoft`）比未知作者更可信
3. **GitHub stars** — 检查源仓库，低于 100 stars 的技能应持怀疑态度

### 第五步：向用户呈现选项

找到相关技能时，向用户呈现：

1. 技能名称和功能说明
2. 安装量和来源
3. 可执行的 install 命令
4. skills.sh 上的了解更多链接

示例回复：

```
找到一个可能有帮助的技能！"react-best-practices" 提供
Vercel Engineering 的 React 和 Next.js 性能优化指南。
（185K 安装）

安装命令：
npx skills add vercel-labs/agent-skills@react-best-practices

了解更多：https://skills.sh/vercel-labs/agent-skills/react-best-practices
```

### 第六步：按需安装

用户想安装时，可代为安装：

```bash
npx skills add <owner/repo@skill> -g -y
```

`-g` 全局安装（用户级），`-y` 跳过确认提示。

## 常见技能类别

| 类别 | 示例查询 |
|------|---------|
| Web 开发 | react, nextjs, typescript, css, tailwind |
| 测试 | testing, jest, playwright, e2e |
| DevOps | deploy, docker, kubernetes, ci-cd |
| 文档 | docs, readme, changelog, api-docs |
| 代码质量 | review, lint, refactor, best-practices |
| 设计 | ui, ux, design-system, accessibility |
| 效率 | workflow, automation, git |

## 搜索技巧

1. **用具体关键词**："react testing" 比 "testing" 更好
2. **尝试替代词**："deploy" 不行试 "deployment" 或 "ci-cd"
3. **检查热门来源**：很多技能来自 `vercel-labs/agent-skills` 或 `ComposioHQ/awesome-claude-skills`

## 输出格式

- 搜索结果：技能名 + 安装量 + 来源 + install 命令
- 无结果时：明说未找到，建议直接帮助或创建新技能

## 兜底

- 未找到相关技能 → 明说"未找到现有技能覆盖此需求"，提供直接帮助，建议用户用 `npx skills init` 创建自己的技能
- 搜索结果全低质量（<100 安装、未知来源）→ 明说"未找到可信技能"，提供直接帮助
