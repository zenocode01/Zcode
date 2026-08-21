# pi-agent 插件三合一完整支持 — 设计文档

- 日期：2026-08-21
- 状态：已批准（brainstorming 方案经用户确认）
- 关联工单：T-027
- 依赖：无（与 T-026 相互独立）

## 1. 背景与目标

zcode 对 pi-agent 目前只有技能软链说明（`adapters/platforms/pi/INSTALL.md`），无深度插件。pi-agent 提供三层插件能力：Extension（TS 模块，`pi.registerTool/registerCommand/on`）、Pi Package（`package.json` 加 `pi` 键打包分发）、Skills（SKILL.md，已支持）。

**目标**：实现"三合一完整支持"——命令透传（人用）+ LLM 工具注册（AI 用）+ Pi Package 打包（分发用），让 zcode 能力在 pi 内部可调、可分发。

## 2. 非目标（YAGNI 削减）

- 不把 zcode 的**有副作用写操作**（`ticket begin/close`、git 写操作、memory 写入）暴露为 AI 自动工具——只做命令透传，由人显式触发。
- 不做其他平台（Claude/Cursor/Codex…）的深度插件——本工单聚焦 pi；T-001 统筹其余平台。
- 不在 TS 里重实现 zcode 逻辑——一律委托本机 `zcode` CLI。

## 3. 方案（三合一）

### 3.1 命令透传（人用）

`adapters/platforms/pi/extension/index.ts` 注册 `/zcode <子命令>` 命令：

- handler 用 `node:child_process` 调本机 `zcode` CLI，结果经 `ctx.ui.setWidget()` 显示在编辑区上方（可滚动）。
- **三级定位 zcode**：`zcode`（PATH）→ `~/.local/bin/zcode` → `<repo>/.venv/bin/zcode`；再退回 `python3 -m zcode`。均不可用时 `ctx.ui.notify` 提示安装法（`bash scripts/install.sh`），不崩溃、不阻塞 pi 启动。

### 3.2 LLM 工具注册（AI 用）

`pi.registerTool()` 只注册**只读、幂等**工具（避免 AI 误操作）：

| 工具 | 对应 CLI | 用途 |
|---|---|---|
| `zcode_ticket_context` | `ticket context` | AI 接手仓库先看工单状态 |
| `zcode_memory_search` | `memory search <query>` | 检索跨会话记忆 |
| `zcode_skills_list` | `skills list` | 查可用技能 |
| `zcode_glossary` | `ticket gloss` | 查术语表 |

工具 schema 用 `typebox` 定义参数；内部走同一 `zcode.ts` 助手调 CLI，返回结构化文本给 LLM。

### 3.3 Pi Package 打包（分发用）

根 `package.json` 增加：

```json
"keywords": [..., "pi-package"],
"pi": {
  "extensions": ["./adapters/platforms/pi/extension"],
  "skills": ["./skills"]
}
```

效果：`pi install git:github.com/zenocode01/Zcode.git` 或本地路径一键装齐技能 + 扩展；INSTALL.md 同步安装/卸载说明。

## 4. 目录与文件清单

```
adapters/platforms/pi/INSTALL.md            # 修改：pi install 用法 + extension 说明
adapters/platforms/pi/extension/index.ts    # 新增：/zcode 命令 + zcode_* 工具
adapters/platforms/pi/extension/zcode.ts    # 新增：定位/执行 zcode CLI + 解析
adapters/platforms/pi/extension/package.json# 新增：peerDeps（pi-coding-agent/typebox）
package.json                                # 修改：加 pi 键 + pi-package keyword
README.md / AGENTS.md / CHANGELOG.md         # 修改：文档同步（随工单）
```

## 5. 安全与健壮性

- 工具层只读、无副作用；写操作只走命令透传。
- extension 无 zcode CLI 时降级为提示，不影响 pi 启动。
- 遵循 pi 安全要求：extension 只从可信来源安装（README/INSTALL 明示）。

## 6. 测试策略

- extension 为 TS 模块，不纳入 Python `unittest` 门禁；通过**手动冒烟清单**验证：`pi -e extension` 加载、`/zcode skills list` 输出、`zcode_*` 工具被 LLM 调用。
- `zcode.ts` 的 zcode 定位/执行逻辑抽成可单测的纯函数（可选 vitest，不强制入主门禁）。
- 回归：Python 侧 84 用例不受影响；`marketplace.json`/`package.json` 版本一致性由现有校验覆盖。

## 7. 验收标准

1. `pi -e adapters/platforms/pi/extension/index.ts` 可加载，`/zcode skills list` 在 pi 内展示技能清单。
2. `zcode_*` 4 个工具注册成功，AI 可调用 `zcode_ticket_context` 拿到工单摘要。
3. `pi install <本地路径或 git>` 能装齐 skills + extension。
4. zcode 未安装时 extension 提示装法、不崩溃。

## 8. 风险与权衡

| 风险 | 缓解 |
|---|---|
| `@earendil-works/pi-coding-agent` / `typebox` 为 peerDependency，需 pi 运行时提供 | 按 packages.md 规范列 `peerDependencies: ["*"]`，不打包 |
| zcode CLI 未在 PATH（Windows/venv 差异） | 三级定位 + `python3 -m zcode` 兜底 + 提示 |
| AI 自动调用工具的安全面 | 只读工具白名单；写操作仅命令透传 |
| pi 版本 API 差异 | 以当前官方文档（extensions.md / packages.md）为准，实现时真机验证 |
