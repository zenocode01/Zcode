# 工单

工作拆解列表。每个工单一个块，格式：

```markdown
### T-XXX 工单标题
Status: backlog          # backlog / in-progress / review / done / blocked
Depends: T-00X           # 可选的依赖（多个用逗号分隔）
Resolution:              # 修复情况（根因+修复+验证），close 前用 zcode ticket resolve 填写
- [ ] 任务项 1
- [ ] 任务项 2
```

> 状态锚点行（`Status:` / `Depends:` / `Resolution:`）由脚本解析，**不要手动改**，用 `zcode ticket` 命令流转。
> 真实工单用 `## T-XXX` 开头（二级标题）；上面的示例用 `###` 仅为展示，不会被解析。

## 待办区
<!-- 在此补充工单 -->

## T-001 Phase 4: 其余平台深度插件
Status: backlog

## T-002 Phase 4: 技能市场发布通道
Status: backlog

## T-003 启用工单工作台于本仓库
Resolution: 根因: 仓库无工作台纪律; 修复: init --existing 铺骨架+协议并入 AGENTS.md+全局技能同步; 验证: validate/回归通过
Status: done

## T-004 同步 README 与 AGENTS.md 文档
Resolution: 根因: README/AGENTS.md 未反映工单工作台落地; 修复: 技能数 11→12、目录结构补 tickets/STATUS/.vibe、新增 ticket 命令与工作台 bullet、测试命令更新; 验证: market validate 12/12 + unittest 4/4
Status: done

## T-005 测试补齐与回归防线
Resolution: 根因: 测试仅 1 文件 4 用例, 核心模块无回归保护; 修复: test_ticket 33 用例+test_modules 17 用例, check-commit 增加测试门禁(TestCommand 提交时执行, git config zcode.test-gate false 可关), 修复 Depends 解析未 strip 空格移植 bug; 验证: 54 用例全绿, 坏测试提交被 hook 真实拦截
Status: done

## T-006 记录 CHANGELOG + 文档类改动不再阻塞 begin
Resolution: 根因: T-005 遗漏 CHANGELOG, 且文档改动反复阻塞 begin(3 次); 修复: CHANGELOG 0.2.1 条目(54 用例/测试门禁/Depends bug) + README 版本引用同步 + STATE_PREFIXES 纳入文档类(README/CHANGELOG/AGENTS/docs) + repo_clean 测试; 验证: 55 用例全绿
Status: review
