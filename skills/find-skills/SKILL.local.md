---
name: find-skills
description: 技能发现——用户找技能时，搜索 skills.sh 生态并验证质量，呈现可信选项。
---

# find-skills（本地精简版）

## 何时使用

用户问"找 X 技能"、"有 X 的技能吗"、"怎么做 X"、或表达想要某类帮助。

## 工作流程

1. **理解需求**：识别领域 + 具体任务
2. **先查排行榜**：https://skills.sh/ 看是否有知名技能
3. **搜索**：`npx skills find <关键词>`
4. **验证质量**：安装量≥1K、来源可信（vercel-labs/anthropics/microsoft）、GitHub stars≥100
5. **呈现选项**：技能名 + 安装量 + install 命令 + skills.sh 链接
6. **按需安装**：`npx skills add <owner/repo@skill> -g -y`

## 搜索技巧

- 用具体关键词（"react testing" > "testing"）
- 尝试替代词（deploy → deployment → ci-cd）
- 热门来源：vercel-labs/agent-skills, ComposioHQ/awesome-claude-skills

## 输出格式

```
找到：<技能名>（<安装量> 安装，来源 <owner>）
安装：npx skills add <owner/repo@skill>
链接：https://skills.sh/...
```

## 兜底

- 未找到 → 明说"未找到现有技能"，直接帮助或建议 `npx skills init`
- 全低质量 → 明说"未找到可信技能"，直接帮助
