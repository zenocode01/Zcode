# skills/ — 核心技能库（Layer 1）

每个技能解决一个具体的"翻车场景"，松散独立、可随意组合，Agent 在合适语境下自动加载（model-invoked）。

## 技能清单

| 技能 | 类别 | 说明 | 版本 |
|------|------|------|------|
| `grill-me` | 需求对齐 | 设计树逐轮拷问，挖沉默假设（仅用户调用） | 标准 + 本地精简 |
| `brainstorming` | 需求对齐 | 创造性工作前必用：澄清→方案→批准→设计文档 | 标准 + 本地精简 |
| `writing-plans` | 规划 | 拆文件结构清晰、bite-sized、每任务带测试的计划 | 标准 + 本地精简 |
| `tdd` | 测试驱动 | 红绿重构流程 | 标准 + 本地精简 |
| `diagnose` | 调试 | 紧致反馈回路 + 排序假设 + 回归测试 | 标准 + 本地精简 |
| `code-review` | 代码审查 | SHA 派审 + 分级反馈处理 | 标准 + 本地精简 |
| `improve-arch` | 架构治理 | 浅模块→深模块，候选报告 + 逐项决策（仅用户调用） | 标准 + 本地精简 |
| `handoff` | 会话接力 | 会话开始读快照恢复、结束存快照（目标/决策/验证） | 标准 + 本地精简 |
| `subagent-driven-development` | 子代理编排 | 每任务派独立子代理 + 逐任务审查 + 5 轮修复 cap | 标准 + 本地精简 |

**技能链依赖**（移植自 Superpowers）：`brainstorming` → `writing-plans` →（执行）→ `code-review`，交接点必须保留。

## 编写规范

1. **目录结构**：`skills/<name>/`，技能名 `name` 必须匹配 `^[a-z0-9]+(-[a-z0-9]+)*$`（opencode 约束），且与目录名一致。
2. **双版本**：每个技能目录下两份文件，缺一不可：
   - `SKILL.md` — 标准版（云端/强模型），可含背景解释、8-10 步
   - `SKILL.local.md` — 本地精简版（本地小模型），≤3K tokens、≤5-7 步、一行一字段、显式兜底
3. **frontmatter**：每份文件以 YAML frontmatter 开头，至少含 `name` 和 `description`（description 一句话说明何时用，供模型自动加载判断）。
4. **正文结构**：`何时使用` → `工作流程`（编号步骤）→ `输出格式` → `兜底`。
5. **1 层深约束**：所有工具只扫 `skills/<name>/SKILL.md` 一层，不要嵌套子技能目录。

## 模板

复制 `_template/` 作为新技能起点：

```bash
cp -r skills/_template skills/<your-skill-name>
```

## 技能级记忆（Layer 3）

每个技能目录下的 `.memory/`（**本地运行数据，不提交 git**）：

| 文件 | 内容 | 回写方式 |
|------|------|---------|
| `experience.log` | 每次使用经验：日期/场景/结果/一句话教训 | 模板化追加，低频批量 |
| `improvements.md` | 累积改进建议（达阈值回写 SKILL.md） | 复盘时记录 |
| `context-snapshot.json` | 项目上下文快照（固定 schema） | 由适配层按规则收集，不依赖模型生成 |

- 模板见 `skills/_template/.memory/`，新技能复制 `_template/` 时自带。
- 全局记忆（跨项目技能经验）走 `zcode memory`（mem0，~/.zcode/memory）；项目内 `.memory/` 只放轻量快照。
