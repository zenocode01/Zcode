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

## T-011 三系统分工: handoff×mem0×workbench 去重联动
Resolution: 根因: workbench×handoff×mem0 三系统首次同仓, 进行中/决策/验证双写漂移, 无联动; 修复: handoff save 自动引用工单状态(缺省自动传参覆盖), 三技能接手路径统一(先 ticket context 后 handoff load), AGENTS/README 三系统职责表, 测试 4 新增; 验证: 62 用例绿, 实机 handoff 自动带出 T-011
Status: done

## T-012 通俗版使用说明: 面向非技术读者的功能与框架说明
Resolution: 根因: 无面向非技术读者的文档, README 面向开发者门槛高; 修复: docs/通俗说明.md(类比讲解: 员工手册/施工看板/记事本, 四层框架, 高频操作, 小词典), README 顶部引导入口+目录结构同步; 验证: 62 用例绿
Status: done

## T-013 术语表欠账补齐 + 登记时机改为 close 前人工核对
Resolution: 根因: 术语表登记时机是软约束(validate 只拦空表/格式), 13 工单仅 2 词条欠账明显; 修复: 补登 12 条核心术语(工单/阶段/守卫/锚点/状态机/会话接力/测试门禁/变更日志/适配层/记忆层/验证证据/close收尾), 分类修正(术语表从'命令自动管理'移入'close 前人工核对', 写入命令自动但登记决策人工), workbench 双版本/模板/协议段同步; 验证: 62 用例绿, validate 过
Status: done

## T-014 普通用户实操手册: 零基础照做指南
Resolution: 根因: 通俗说明只讲概念无操作步骤, 无零基础实操指南; 修复: docs/使用手册.md(安装4步/建工作台/完整走一遍/对话驱动/看进度/接力/FAQ/速查表), README 入口引导+目录结构同步; 验证: 62 用例绿
Status: done

## T-015 上手体验优化: init 交互引导 + --existing 自动并入协议 + CLI 全局安装
Resolution: 根因: 新项目要手动编辑 CONTEXT/AGENTS, --existing 提示人工并入协议段, install.sh 不装 CLI; 修复: init 交互引导 Domain/TestCommand(非交互跳过), --existing 自动追加协议段到 AGENTS.md(幂等), install.sh 装 ~/.local/bin/zcode 包装器, 手册/README 更新 1 分钟上手路径; 验证: 64 用例绿, 实机嵌入验证通过
Status: done

## T-016 Windows 跨平台支持: install.ps1 + hook 宿主适配 + 测试/文档
Resolution: 根因: 安装/钩子/文档仅 Linux, Windows 用户无法使用; 修复: scripts/install.ps1(Junction/复制免管理员+zcode.cmd/ps1 包装器+用户 PATH+配置), 模板 hook 跨平台宿主(Unix 用 zcode/python, Windows 经 powershell.exe 调 zcode.cmd), git config zcode.cli 路径加引号(Windows 空格路径), 测试适配(权限断言/分支名动态), README/使用手册/AGENTS Windows 分支; 验证: 64 用例绿, hook sh 语法过, ps1 待 Windows 真机验证
Status: done

## T-017 pwsh 真机验证 install.ps1 + 修复路径 bug
Resolution: 根因: install.ps1 用 $PSScriptRoot 定位技能目录(实为 scripts/ 而非仓库根), 且从未真机验证; 修复: $src 改为仓库根(Split-Path -Parent); 验证: pwsh 7.6.4 已装, Unix 分支实跑通过, Windows 分支模拟($env:OS=Windows_NT)通过(Junction 失败退复制), 空 HOME 全量 12 技能安装成功, zcode.cmd/ps1 生成, 包装器 zcode 命令可用
Status: done

## T-018 完整测试发现的 3 个缺陷修复
Resolution: 根因: ① adapters/zcode 缺 __main__.py 导致 python -m zcode 失败(npm 入口 bin/zcode.js 依赖它); ② install.sh UNINSTALL 分支忽略 --project 误删全局 ~/.agents/skills; ③ _auto_commit_state_files 对不存在的 CHANGELOG.md 执行 git add exit 128 静默失败致 close 后工作区残留; 修复: ① 新增 __main__.py; ② 卸载分支支持项目级; ③ add 前过滤不存在的路径; 验证: 67 用例绿(含 3 新增回归), 真机验证 python -m zcode/项目级卸载仅动项目/新项目 close 后工作区干净, 全局软链已恢复
Status: done
