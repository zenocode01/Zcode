# Changelog

本项目从构思到四层架构落地（Phase 1-4）的变更记录。

## [未发布]

**更新 ask commit 提示**：移除过时的「手动 transition」说明，补充 phase review 自动同步行为。

## [0.4.2] - 2026-08-31

**phase 命令自动同步 ticket Status**：根因: cmd_phase 只更新 CONTEXT.md 的 Phase 锚点，不更新 tickets.md 的 ticket Status；两状态机完全解耦，用户 phase review --green 后忘记手动 transition T-XXX review，pre-commit hook 拦截提交; 修复: 新增 _sync_ticket_status()——Phase→review 时自动将 ticket 从 in-progress 过渡到 review，Phase→commit 时自动补过渡; 验证: 待回归

## [0.4.1] - 2026-08-31
**新增 find-skills 核心技能**：根因: 用户无法从 skills.sh 生态搜索安装新技能; 修复: 新增 skills/find-skills/SKILL.md(标准版)+SKILL.local.md(本地精简版), 从 vercel-labs/skills 移植, 支持 npx skills find/add/update 搜索验证安装技能; 同步更新 marketplace.json(count 12→13, version 0.4.1)、skills/README.md(技能清单加 find-skills)、ask-zcode/SKILL.md(入口匝道加 find-skills 路由); 验证: marketplace.json 格式校验通过, 13 技能清单完整

**使用手册补充 git/release/pi 插件说明**（T-029）：根因: 使用手册未覆盖 0.4.0 新增的 git/release/pi 插件三功能; 修复: docs/使用手册.md 新增第 7 节(zcode git 可视化+逐条命令)/第 8 节(zcode release 版本发布)/第 9 节(pi-agent 插件), 原 FAQ/速查表顺延为 10/11, 同步第 0 节导览与速查表、FAQ; 验证: 章节编号 0-11 连续, 速查表含 git/release 命令

## [0.4.0] - 2026-08-21
**zcode release 版本迭代工具**（T-028）：根因: 版本号散落五处人工维护+CHANGELOG 关单自动 bump 与代码版本脱节(0.3.16 vs 0.3.8)+marketplace.py 三处写死 0.1.0; 修复: 新增 release.py(zcode release patch/minor/major/X.Y.Z, 统一写五处版本号+归并未发布区块为正式版本+打 tag+可选 push)+marketplace.py 三处 0.1.0 改读 __version__+ticket._auto_changelog 改写未发布区块不再 bump+cli 注册 release; 验证: 123 用例全绿(新增 12 release), zcode release --dry-run 输出计划, marketplace build version=0.3.8, close 写未发布区块测试更新

**zcode git 交互式 TUI 仓库管理**（T-026）：根因: zcode 无面向用户的 git 管理命令, git 能力仅内部使用(update/ticket/hooks); 修复: 新增 gitcore.py 零依赖逻辑层(status/log/branch/stash/diff 解析+写操作封装+危险命令识别) + gitcli.py 非 TTY 逐条命令彩色渲染 + gittui.py textual 全屏 TUI(8 面板+空格暂存+冲突 ours/theirs 解决) + cli.py 注册 TTY 分发 + pyproject 加 textual 依赖; 验证: 111 用例全绿(新增 21 gitcore+6 gitcli), textual 8.2.8 兼容 Python 3.14, TUI 冒烟 8 面板渲染+stage/unstage+冲突 ours 解决, 非 TTY zcode git status/log 正常

**pi-agent 插件三合一完整支持**（T-027）：根因: zcode 对 pi-agent 仅技能软链说明(INSTALL.md), 无深度插件; 修复: 新增 adapters/platforms/pi/extension 三合一插件(/zcode 命令透传 + 4 个只读工具 zcode_ticket_context/memory_search/skills_list/glossary + package.json pi 键打包), 根 package.json 加 pi-package, INSTALL/README/AGENTS/术语表同步; 验证: 84 用例全绿, tsx 验证 runZcode, pi -e 加载成功, zcode_skills_list/zcode_ticket_context 工具被 LLM 真实调用, pi install 打包识别成功

**zcode update 自更新命令**（T-025）：根因: CLI 无自更新命令, 用户需手动 git pull + 重装多步; 实现: 新增 adapters/zcode/update.py + zcode update [--dry-run]——前置检查(工作区干净, 未提交改动拒绝防覆盖)→ git fetch(失败附网络/凭据提示)→ rev-list 已最新退出→ pull --ff-only→ 当前解释器 pip install -e→ npm link(可选, 失败仅警告)→ scripts/install.sh→ 变更摘要; 每步失败即停报告已完成步骤+重跑指引; 验证: 84 用例绿(新增 6: precheck 脏/净/dry-run 零执行/成功序列/已最新退出/失败中止), 真机 dry-run 与脏工作区拦截实测通过

**zcode version 子命令 + __version__ 第五处版本统一**（T-024）：根因: CLI 无版本查看命令, 且 __init__.py __version__ 停在 0.1.0(T-019 版本统一四文件漏第五处); 修复: __version__ 同步 0.3.8(与 pyproject/package.json/marketplace/plugin 一致), 注册 zcode version 子命令输出代码内版本; 验证: 78 用例绿(新增 2: __version__ 与 pyproject 一致性防漂移/version 命令输出格式), zcode version 输出 zcode 0.3.8

**install.sh 包装器生成逻辑修复: 优先项目 venv**（T-023）：根因: install.sh 的 install_cli 写死 exec python3(系统解释器), 且包检查基于系统 python3; 重跑 install.sh 会覆盖手工修好的 venv 包装器(Bug 1 复发, ModuleNotFoundError); 修复: 解释器优先 REPO_ROOT/.venv/bin/python(PEP 668 环境), 回退 python3; 包装器与检查逻辑同步用实际解释器; 验证: 重跑 install.sh 后包装器指向 venv 且任意目录 zcode 可用(无 ModuleNotFoundError), 76 用例全绿

**memory add 静默 0 条: infer 提取失败自动降级 + 提示**（T-022）：根因: MemStore.add 在 infer(simplified) 模式下直接透传 mem0, LLM 提取返回 0 条时静默返回空 results, CLI 只打印『已写入 0 条记忆』无任何提示/降级, 用户感知为写入失败且记忆丢失; 修复: ① MemStore.add 在 infer 且提取 0 条时自动降级 L0(原文纯 embedding 第二次写入, 参数透传), 返回 dict 附 degraded=True; ② CLI 检测 degraded 向 stderr 打印明确提示; 验证: 76 用例绿(新增 4: 降级两次调用/成功不降级/L0 不重试/CLI 提示), 真机 memory add 触发降级提示+写入成功; 已知环境限制: BM25 encoder 加载失败(fastembed 下载被 Steam++ 证书拦截), 检索降级纯 embedding 不影响核心

**gloss list 报「术语『list』不存在」应提示用法**（T-021）：根因: ① cmd_add 条件反写——有参时取空串、无参才提问(dep_input/body), Depends 与描述参数静默丢失(登记工单时描述从未写入); ② gloss list 把 list 当术语查询报不存在, 查询未命中提示不完整; ③ add --help 把 --help 当标题建空单; 修复: ① 条件修正为有参取参、无参提问; ② gloss list/ls 识别为列出全部, 未命中提示完整用法(列出/添加); ③ run() 统一处理子命令 -h/--help 显示帮助, show_help 同步 add/gloss 用法; 验证: 72 用例绿(新增 4: add 依赖+描述写入/--help 不建单/gloss list 列出/未命中提示), 真机冒烟 add 带参写入成功

**close 流程健壮性修复: 中间态崩溃 + CHANGELOG 静默跳过**（T-020）：根因: ① cmd_close 在合并分支前执行 _auto_changelog 改 CHANGELOG.md, 而 repo_clean 只查非状态文件(CHANGELOG 在 STATE_PREFIXES 内), CHANGELOG 为分支独有文件时 git switch 被拒, close 中止在中间态(工单仍 review/条目已追加/分支未合并)且无恢复指引; ② _auto_changelog 文件缺失时直接 return None 不创建不提示, 与 SKILL.md 承诺不符; ③ repo_clean 命名误导(叫整仓干净实查源码); 修复: ① close 重排——先合并分支(switch 前预检 base 不存在的脏文件并阻止+指引, switch/merge 失败附恢复指引, 可幂等重跑)再补录 CHANGELOG; ② _auto_changelog 缺失时创建 [0.1.0] 基线并提示; ③ repo_clean 改名 dirty_source_paths 返回路径列表, 错误文案列具体文件; 验证: 68 用例绿(新增 Bug2 回归分支独有 CHANGELOG/预检脏文件, Bug3 基线创建, 函数改名 3 处)

## [0.3.8] - 2026-08-07
**正式发布 0.3.8**（T-019）：package.json/pyproject.toml/marketplace.json/plugin.json 版本统一 0.1.0→0.3.8(与 CHANGELOG 对齐); 验证: 67 用例绿

**完整测试发现的 3 个缺陷修复**（T-018）：根因: ① adapters/zcode 缺 __main__.py 导致 python -m zcode 失败(npm 入口 bin/zcode.js 依赖它); ② install.sh UNINSTALL 分支忽略 --project 误删全局 ~/.agents/skills; ③ _auto_commit_state_files 对不存在的 CHANGELOG.md 执行 git add exit 128 静默失败致 close 后工作区残留; 修复: ① 新增 __main__.py; ② 卸载分支支持项目级; ③ add 前过滤不存在的路径; 验证: 67 用例绿(含 3 新增回归), 真机验证 python -m zcode/项目级卸载仅动项目/新项目 close 后工作区干净, 全局软链已恢复

## [0.3.7] - 2026-08-07
**pwsh 真机验证 install.ps1 + 修复路径 bug**（T-017）：根因: install.ps1 用 $PSScriptRoot 定位技能目录(实为 scripts/ 而非仓库根), 且从未真机验证; 修复: $src 改为仓库根(Split-Path -Parent); 验证: pwsh 7.6.4 已装, Unix 分支实跑通过, Windows 分支模拟($env:OS=Windows_NT)通过(Junction 失败退复制), 空 HOME 全量 12 技能安装成功, zcode.cmd/ps1 生成, 包装器 zcode 命令可用

## [0.3.6] - 2026-08-07
**Windows 跨平台支持: install.ps1 + hook 宿主适配 + 测试/文档**（T-016）：根因: 安装/钩子/文档仅 Linux, Windows 用户无法使用; 修复: scripts/install.ps1(Junction/复制免管理员+zcode.cmd/ps1 包装器+用户 PATH+配置), 模板 hook 跨平台宿主(Unix 用 zcode/python, Windows 经 powershell.exe 调 zcode.cmd), git config zcode.cli 路径加引号(Windows 空格路径), 测试适配(权限断言/分支名动态), README/使用手册/AGENTS Windows 分支; 验证: 64 用例绿, hook sh 语法过, ps1 待 Windows 真机验证

## [0.3.5] - 2026-08-07
**上手体验优化: init 交互引导 + --existing 自动并入协议 + CLI 全局安装**（T-015）：根因: 新项目要手动编辑 CONTEXT/AGENTS, --existing 提示人工并入协议段, install.sh 不装 CLI; 修复: init 交互引导 Domain/TestCommand(非交互跳过), --existing 自动追加协议段到 AGENTS.md(幂等), install.sh 装 ~/.local/bin/zcode 包装器, 手册/README 更新 1 分钟上手路径; 验证: 64 用例绿, 实机嵌入验证通过

## [0.3.4] - 2026-08-07
**普通用户实操手册: 零基础照做指南**（T-014）：根因: 通俗说明只讲概念无操作步骤, 无零基础实操指南; 修复: docs/使用手册.md(安装4步/建工作台/完整走一遍/对话驱动/看进度/接力/FAQ/速查表), README 入口引导+目录结构同步; 验证: 62 用例绿

## [0.3.3] - 2026-08-07
**术语表欠账补齐 + 登记时机改为 close 前人工核对**（T-013）：根因: 术语表登记时机是软约束(validate 只拦空表/格式), 13 工单仅 2 词条欠账明显; 修复: 补登 12 条核心术语(工单/阶段/守卫/锚点/状态机/会话接力/测试门禁/变更日志/适配层/记忆层/验证证据/close收尾), 分类修正(术语表从'命令自动管理'移入'close 前人工核对', 写入命令自动但登记决策人工), workbench 双版本/模板/协议段同步; 验证: 62 用例绿, validate 过

## [0.3.2] - 2026-08-07
**通俗版使用说明: 面向非技术读者的功能与框架说明**（T-012）：根因: 无面向非技术读者的文档, README 面向开发者门槛高; 修复: docs/通俗说明.md(类比讲解: 员工手册/施工看板/记事本, 四层框架, 高频操作, 小词典), README 顶部引导入口+目录结构同步; 验证: 62 用例绿

## [0.3.1] - 2026-08-07
**三系统分工: handoff×mem0×workbench 去重联动**（T-011）：根因: workbench×handoff×mem0 三系统首次同仓, 进行中/决策/验证双写漂移, 无联动; 修复: handoff save 自动引用工单状态(缺省自动传参覆盖), 三技能接手路径统一(先 ticket context 后 handoff load), AGENTS/README 三系统职责表, 测试 4 新增; 验证: 62 用例绿, 实机 handoff 自动带出 T-011

## [0.3.0] - 2026-08-07
**close 自动化**（T-010）：状态文件自动提交 + CHANGELOG 自动补录，消灭"收尾/欠账"类无用工单。

### close 自动收尾（adapters/zcode/ticket.py）
- **状态文件自动提交**：close 后 tickets.md / STATUS.md / docs/CONTEXT.md / 术语表 / `.vibe/` / CHANGELOG.md 自动 `git commit`（`T-XXX 状态收尾`，绕过 hook——属协议内部收尾），工作区保持干净 → 不再需要"状态文件收尾"类工单（原 T-007 场景消失）
- **CHANGELOG 自动补录**：`CHANGELOG.md` 缺本工单号时，close 自动从 Resolution 生成条目（`## [0.x.y+1] - 日期`，版本自动 bump，插入顶部），不再"拒绝+人工补"→ 不再需要"补 CHANGELOG"类工单（原 T-006 场景消失）
- 原守卫语义保留：已有记录不重复追加；无 CHANGELOG 文件不创建；人工写的条目仍被识别

### 文档同步
- `skills/workbench`（双版本）：标准循环第 10 步 close 自动收尾说明；文档同步章节改为"CHANGELOG 自动兜底 + README/AGENTS/技能清单人工核对"
- 模板 `adapters/zcode/templates/ticket/AGENTS.md`：第 8 条 close 自动收尾 / 第 9 条人工同步
- 本仓库 `AGENTS.md` 协议段：第 5 条 close 自动收尾（明示"不再需要收尾类工单"）/ 第 6 条人工同步
- `README.md`：测试条目更新（58 用例 + close 自动收尾）

### 验证
- 59 用例全绿（38 ticket + 17 modules + 4 evoskills）；新增 3 用例：自动补录+提交、不重复追加、无文件不创建

## [0.2.3] - 2026-08-07
**文档同步清单完整化**（T-009）：六类相关文件职责分类 + 修历史欠账。

### 职责分类（workbench 双版本 / 模板 AGENTS.md / 本仓库 AGENTS.md 协议段）
- **命令自动管理**（无需人工，校验拦截）：`tickets.md`、`STATUS.md`、`docs/CONTEXT.md` 锚点、`docs/UBIQUITOUS_LANGUAGE.md`、`.vibe/`
- **人工同步**（随工单提交）：`CHANGELOG.md`（硬强制，close 守卫）＋ `README.md` / `AGENTS.md` / 技能清单（ask-zcode / skills/README / marketplace.json）

### 修欠账
- `AGENTS.md`："无远程仓库" → `origin` 指向 `https://github.com/zenocode01/Zcode.git`；日期 2025-08 → 2026-08
- `README.md`：测试用例 55 → 57；CHANGELOG 引用补 0.2.2；日期 2025-08 → 2026-08

## [0.2.2] - 2026-08-07
**文档同步强制**（T-008）：close 前相关文档必须随工单更新，杜绝"关了单文档没更新"。

### close 守卫（adapters/zcode/ticket.py）
- 仓库存在 `CHANGELOG.md` 时，`zcode ticket close T-XXX` 校验 CHANGELOG 已含 `T-XXX`，缺则拒绝并提示补记
- 新增测试：`test_close_requires_changelog_entry`（缺记录拒绝 / 补记后可 close）、`test_close_allows_no_changelog_file`（无 CHANGELOG 的项目放行）

### 文档同步
- `skills/workbench`（双版本）：标准循环第 10 步 + 新增"文档同步（close 前必须）"章节（CHANGELOG 硬强制 / README / AGENTS / 技能清单）
- 模板 `adapters/zcode/templates/ticket/AGENTS.md`：职责第 8 条 + 修复流程第 7 步加文档同步
- 本仓库 `AGENTS.md` 协议段：第 5 条"close 前文档同步"（CHANGELOG 必须含工单号，README/AGENTS/技能清单随工单提交）；第 4 条补测试门禁
- `README.md`：测试条目更新（55 用例 + 测试门禁 + close 守卫）

### 验证
- 57 用例全绿（36 ticket + 17 modules + 4 evoskills）；T-008 自身完整演示：close 守卫在无 CHANGELOG 记录时拒绝、补记后通过

## [0.2.1] - 2026-08-07
**测试**：测试补齐与回归防线（T-005）——4 用例 → 54 用例 + 提交测试门禁。

### 测试覆盖（unittest 零依赖）
- `adapters/tests/test_ticket.py`（33 用例）：锚点读写、工单/术语表解析、状态机跃迁矩阵、守卫（Domain/验证产物/--green/--red/--pass/--reject）、依赖环检测、STATUS 生成器保鲜（CRLF / GENERATED-BY 注释归一化）、init --existing 不覆盖已有文件、完整命令流集成（begin 自动开分支 + close 自动合并删除）、check-commit 门禁（含开关）
- `adapters/tests/test_modules.py`（17 用例）：workflow 引擎（加载/条件跳过/命令失败传播）、handoff（项目级/全局/空节）、marketplace（12 技能全有效）、profile（必填字段/真实 profile）
- 回归命令：`python3 -m unittest discover -s adapters/tests`

### 提交测试门禁（check-commit）
- 配了 `TestCommand:` 的项目，提交时真实执行测试，失败拦截提交（含最近 3 行错误输出提示）
- 关闭开关：`git config zcode.test-gate false`
- 已验证：坏测试提交被 pre-commit hook 真实拦截（55 tests FAILED → 拦截）

### 修复
- `ticket.py` Depends 锚点解析：元素未 strip 前导空格（vibe-workbench 原版 Trim 了），导致 `Depends: T-001, T-002` 解析出 `" T-002"`——测试抓出的移植 bug

### 验证
- 54/54 用例通过；`zcode market validate` 12/12 通过；坏测试拦截 + 门禁开关端到端验证

## [0.2.0] - 2026-08-07
**新增**：工单驱动开发工作台（Layer 2，vibe-workbench 移植）——双状态机 + 可执行强制。

### 新命令（adapters/zcode/ticket.py + cli.py）
- `zcode ticket <cmd>`：init / add / begin / phase / transition / close / resolve / context / gloss / status / validate / next / log / install / projects / switch / project-add / ask / check-commit
- 两个状态机：Agent 阶段机（analyze→plan→implement→verify→review→commit）+ 工单生命周期机（backlog→in-progress→review→done，blocked→backlog）
- 可执行强制：阶段/流转守卫（非法跃迁拒绝）、依赖守卫与环检测、验证证据（TestCommand 真实执行 + `.vibe/evidence/` 留痕）、STATUS.md 状态自刷新与保鲜拦截、pre-commit hook 提交闸门、分支耦合（begin 自动开 `vibe/T-XXX`、close 自动 merge --no-ff 删除）
- 修复记录（`Resolution:` 锚点，close 前强制）与术语表（`vibe gloss add`，Domain 非空时强制非空）
- 兼容：与 vibe-workbench 文件格式（tickets.md / docs/CONTEXT.md / STATUS.md / `.vibe/`）与 `~/.vibe/projects.json` 注册表完全一致，两 CLI 可混用；STATUS 保鲜判定对生成器注释与 CRLF 行尾归一化

### 新技能与工作流
- `skills/workbench`（SKILL.md + SKILL.local.md）：工单驱动开发技能，入 ask-zcode 路由（匝道 + 独立技能 + 判别条件）
- `workflows/ticket-dev.yaml`：确定性工作流模板（workbench 技能 + context/next 命令 + 循环推进提示）

### 验证
- 端到端全流程：init → add → begin（自动开分支）→ phase 全链路（守卫拦截非法跃迁）→ transition → resolve → commit（pre-commit hook 拦截 Phase=analyze/in-progress 非法提交）→ close（校验 Resolution + 提交 + 自动合并分支）
- `zcode market validate` 12/12 通过

## [0.1.1] - 2026-08-06
**打磨**：EvoSkills 审计闭环修复 + tdd 技能首轮迭代（evoskills 六步循环实战）。

### 引擎修复（adapters/zcode/evoskills.py）
- 审计闭环缺陷：`needs_revision` 仅由历史成功率判定，发布修订版后成功率不变，导致"发布后重审计确认健康度回升"永远无法达成 → 新增 `_revision_published_since_last_issue()`：技能文件在最近失败/改进记录之后被修改过即视为已发布修订版，不再重复报修订，改为等待新样本
- 审计报告新增状态："✓ 已发布修订版，等待新样本"

### 技能迭代（skills/tdd）
- 审计触发：5 次使用 3 成功 2 失败、成功率 60% < 70%（教训：跳过测试直接改引入回归；没建反馈回路浪费两轮）
- 双版本补"启动门槛"：动手前确认反馈回路就绪；紧急修复先写复现测试、性能优化先写基准/特征测试，禁止跳过测试直接改

### 测试（首个测试框架落地）
- `adapters/tests/test_evoskills.py`：审计闭环 4 用例（unittest 零依赖，`python3 -m unittest discover -s adapters/tests`）

### 验证
- 4/4 测试通过；`zcode skill audit tdd` 显示已发布修订版；`zcode market validate` 全部通过

## [0.1.0] - 2025-08-06
**里程碑**：四层架构全部落地 + 真机端到端验证（Qwen3.6-35B / llama.cpp / 256K）。

### 技能库（Layer 1）
- 移植 10 个核心技能，全部**双版本**（`SKILL.md` 云 / `SKILL.local.md` 本地小模型）：
  - Matt Pocock 风格：`grill-me`（设计树拷问）、`tdd`（红绿重构）、`diagnose`（系统化调试）、`improve-arch`（架构治理）
  - Superpowers 风格：`brainstorming`（硬门）、`writing-plans`（No Placeholders）、`code-review`（分级反馈）
  - 自研：`handoff`（会话接力）、`subagent-driven-development`（子代理编排）、`evoskills`（自我迭代）
- `_template/` 双版本模板 + `.memory/` 技能级记忆模板（experience.log / improvements.md / context-snapshot.json）

### 适配层（Layer 0）
- Python 包 `zcode`：profile 能力声明、OpenAI 兼容 Provider（llama.cpp `/v1`）、工具三层降级（L2 原生 / L1 提示词编码 / L0 无工具）、工具映射表（spawn/parallel/todo/review → 8 平台）
- 8 平台适配：Claude Code / Cursor / Codex / Gemini CLI / opencode / Kimi Code / Pi / Reasonix（`INSTALL.md` + 软链接安装）
- `scripts/install.sh`：主目标 `~/.agents/skills`（跨工具事实标准）+ 平台原生目录双保险，幂等可卸载
- npm 分发入口（`bin/zcode.js` + `package.json`）

### 编排（Layer 2）
- 确定性工作流模板（`workflows/feature-dev`）：skill/prompt/command/subagent 四类步骤，外部 runner 驱动
- MetaSkill 自由编排（`metaskills/feature-dev`）：模型生成计划 → 复用执行器；profile `orchestration` 开关（本地默认 deterministic）
- 子代理编排：独立上下文 / ledger 恢复地图 / 逐任务审查（规格+质量）/ 5 轮修复 cap + breaker / 3 个提示词模板

### 记忆与迭代（Layer 3）
- mem0 本地三件套：Qwen3.6-35B（LLM）+ Qwen3-Embedding-8B（自定义 HttpEmbedder，4096 维）+ Qdrant 嵌入式
- 记忆写入四级降级（L0 纯 embedding → L1 简化提取 → L2 容错解析 → L3 批量）；检索零 LLM
- BM25 词形还原 + 实体增强（spaCy en_core_web_sm，经 gitproxy 代理解决国内网络）
- 会话接力：`zcode handoff save/load`（模板化六要素快照，不耗 token）
- EvoSkills 自我迭代：`zcode skill log/audit`（捕获/评估，阈值 70%/2 条）+ 六步循环元技能

### 生态（Phase 4 起步）
- 技能市场：`zcode market list/validate`（marketplace.json + 质量校验：frontmatter/命名/双版本/体积/占位符）
- 深度插件：Claude Code（`.claude-plugin/`）、opencode（permission.skill）、Kimi Code（installed.json）

### 真机验证（2025-08-06）
- 工具调用：tool_level=2（原生 tool calling）✅
- MetaSkill：真实模型自主编排（跳过 grill-me、遵守硬门）✅
- 记忆：add 提取 4 条事实 → search 命中 score 0.81 ✅
- 技能安装：10 技能软链到 `~/.agents/skills/`，幂等验证 ✅

### 关键修复
- L2 原生工具调用的 `tool_calls` 被 `Provider.chat()` 丢弃 → 新增 `chat_message()`
- mem0 provider 白名单校验 → `model_construct` 绕过
- mem0 2.0.17 API 差异（search 用 filters）→ 适配
- 记忆路径 `~` 未展开导致运行时数据误入仓库 → expanduser + `.gitignore` 防护
- 占位符校验误报（TODO vs todo、否定语境）→ 区分大小写 + 语境过滤
