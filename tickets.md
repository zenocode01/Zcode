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
Status: done

## T-007 状态文件收尾入库 + 推送远程
Resolution: 根因: close 后状态文件改动待入库; 修复: 随 T-007 一并提交(tickets/STATUS/CONTEXT/.vibe/log); 验证: 55 用例绿
Status: done

## T-008 close 前文档同步强制: CHANGELOG 必须含工单号
Resolution: 根因: 文档同步靠事后追补(T-005 漏 CHANGELOG 被质疑), 无强制; 修复: close 守卫检查 CHANGELOG 含工单号(缺则拒), workbench/模板/AGENTS/README 同步文档同步条款, 新增 2 测试; 验证: 57 用例绿, 拒绝/放行路径测试覆盖
Status: done

## T-009 文档同步清单完整化: 六文件职责分类 + 修欠账
Resolution: 根因: 文档同步清单只列人工文件, 未说明自动管理文件; 修欠账: AGENTS 无远程仓库过时(有 origin), README 用例数 55→57 且 CHANGELOG 引用缺 0.2.2, 日期 2025→2026; 修复: workbench/模板/协议段补六文件职责分类(A 命令自动管理/B 人工同步), README 版本引用改为指向文件顶部根治数字脱节; 验证: 57 用例绿, market 12/12
Status: done

## T-010 close 自动化: 状态文件自动提交 + CHANGELOG 自动生成, 消灭收尾/欠账工单
Resolution: 根因: close 后状态文件残留+CHANGELOG 欠账, 产生 T-004/T-006/T-007/T-009 类低价值补丁工单; 修复: close 自动提交状态文件(T-XXX 状态收尾, 绕 hook) + CHANGELOG 缺工单号自动从 Resolution 补录(版本自动 bump 不重复); 文档同步; 验证: 59 用例绿, 3 新增用例覆盖
Status: done
