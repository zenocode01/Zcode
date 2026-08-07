# 通用语言词汇表

本文件记录项目的领域术语，消除歧义。当术语有多个含义、命名不清或需要沉淀时，在此补充词条。
词条格式机器可解析（`## 术语` + `- **含义**：` 一行），由 `zcode ticket gloss` 命令管理：
`zcode ticket gloss` 列出、`zcode ticket gloss <术语>` 查询、`zcode ticket gloss add <术语> <定义>` 记录。

### 词条格式

```markdown
## 术语名
- **含义**：一句话定义
- **别名/冲突**：其他叫法或需要澄清的歧义
```

<!-- 在此补充词条（或使用 zcode ticket gloss add <术语> <定义>） -->

## Layer
- **含义**：四层架构的分层: Layer 0 适配/1 技能/2 编排/3 记忆迭代

## workbench
- **含义**：工单驱动开发工作台(zcode ticket): 双状态机+可执行强制, 移植自 vibe-workbench

## 工单
- **含义**：一件待办事项, 编号 T-XXX, 状态机管理(backlog/in-progress/review/done/blocked)

## 阶段
- **含义**：工单固定流程: analyze→plan→implement→verify→review→commit

## 守卫
- **含义**：流程中不许跳步的强制检查(如无测试不许 verify 通过)

## 锚点
- **含义**：文档中机器可读的关键行(Phase:/Status:/Resolution: 等), 命令维护

## 状态机
- **含义**：Agent 阶段机+工单生命周期机, 合法跃迁由命令校验

## 会话接力
- **含义**：handoff: 交接班快照, 让未来会话恢复目标/决策/验证

## 测试门禁
- **含义**：pre-commit 提交前真实跑测试, 失败拦截; git config zcode.test-gate false 可关

## 变更日志
- **含义**：CHANGELOG.md: 每次工单 close 自动补录, 版本自动 bump

## 适配层
- **含义**：Layer 0: 万能插座, 一套技能软链 8 平台

## 记忆层
- **含义**：Layer 3: mem0 语义记忆, 与术语表互补(自由事实检索)

## 验证证据
- **含义**：.vibe/evidence/: TestCommand 真实执行的退出码+输出留痕

## close收尾
- **含义**：close 自动: CHANGELOG 补录+状态文件提交, 工作区常净
