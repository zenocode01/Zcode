# 实现计划 — pi-agent 插件三合一完整支持（T-027）

- 日期：2026-08-21
- 关联 spec：`docs/superpowers/specs/2026-08-21-pi-agent-plugin-design.md`
- 关联工单：T-027

## Goal

为 pi-agent 提供三合一插件支持：`/zcode` 命令透传（人用）+ `zcode_*` 只读工具（AI 用）+ Pi Package 打包（`pi install` 分发）。

## Architecture

```
adapters/platforms/pi/extension/index.ts     # 入口：/zcode 命令 + zcode_* 工具
adapters/platforms/pi/extension/zcode.ts     # 助手：定位/执行 zcode CLI
adapters/platforms/pi/extension/package.json # peerDeps（pi-coding-agent / typebox）
package.json                                 # 加 pi 键 + pi-package keyword
adapters/platforms/pi/INSTALL.md             # 更新安装说明
```

依赖方向：`index.ts → zcode.ts → 本机 zcode CLI（child_process）`。不在 TS 里重实现 zcode 逻辑。

## Tech Stack

- TypeScript（pi extension 经 jiti 加载，无需编译）
- `@earendil-works/pi-coding-agent` + `typebox`（peerDependency，pi 运行时提供）
- Node 内建 `node:child_process` 调 zcode CLI

## Global Constraints

1. 工具层（`zcode_*`）只读、幂等、无副作用；有副作用写操作（ticket begin/close、git 写、memory add）只走 `/zcode` 命令透传，由人显式触发。
2. zcode CLI 不可用时 extension 降级为 `ctx.ui.notify` 提示，不崩溃、不阻塞 pi 启动。
3. 遵循 packages.md：`@earendil-works/pi-coding-agent`、`typebox` 列 `peerDependencies` 用 `"*"`，不打包进 node_modules。
4. API 以 pi 官方文档 `extensions.md` / `packages.md`（本机路径 `~/.nvm/versions/node/v24.19.0/lib/node_modules/@earendil-works/pi-coding-agent/docs/`）为准。
5. 中文提示与描述（项目文档语言约定）；代码注释中文。
6. 每任务以「冒烟验证 + commit」结尾（extension 无 Python 单测，见 spec 第 6 节）。

---

## Task 1 — extension 目录骨架 + peerDeps 声明

**Files**
- Create `adapters/platforms/pi/extension/package.json`
- Create `adapters/platforms/pi/extension/zcode.ts`（本任务先放空导出，Task 2 填实现）

**Interfaces**
- Produces: `package.json` 的 `peerDependencies` 声明

**步骤**

- [ ] 写 `package.json`：

```json
{
  "name": "zcode-pi-extension",
  "version": "0.3.8",
  "description": "Zcode 技能的 pi-agent 深度插件：/zcode 命令透传 + zcode_* 只读工具",
  "type": "module",
  "peerDependencies": {
    "@earendil-works/pi-coding-agent": "*",
    "typebox": "*"
  }
}
```

- [ ] 写 `zcode.ts` 骨架：

```typescript
// zcode CLI 定位与执行助手（Task 2 填实现）
export interface ZcodeResult {
  ok: boolean;
  output: string;
  code: number;
}

export function runZcode(_args: string[]): ZcodeResult {
  throw new Error("尚未实现");
}
```

- [ ] 冒烟：`node -e "import('./adapters/platforms/pi/extension/zcode.ts')"` 不报语法错（jiti 下才真正执行）
- [ ] commit

---

## Task 2 — zcode.ts：定位与执行 zcode CLI

**Files**
- Modify `adapters/platforms/pi/extension/zcode.ts`

**Interfaces**
- Produces:
  - `export function runZcode(args: string[]): ZcodeResult` — 按候选序列尝试执行，返回 `{ok, output, code}`

**候选序列**：`["zcode"]`（PATH）→ `[join(homedir(), ".local", "bin", "zcode")]` → `["python3", "-m", "zcode"]`。任一 `spawnSync` 的 `error.code === "ENOENT"` 则试下一个；非 ENOENT 错误直接返回失败；命令存在则返回其退出码与合并输出。

**步骤**

- [ ] 实现 `runZcode`：

```typescript
import { spawnSync } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";

export interface ZcodeResult {
  ok: boolean;
  output: string;
  code: number;
}

const CANDIDATES: string[][] = [
  ["zcode"],
  [join(homedir(), ".local", "bin", "zcode")],
  ["python3", "-m", "zcode"],
];

export function runZcode(args: string[]): ZcodeResult {
  for (const cmd of CANDIDATES) {
    const r = spawnSync(cmd[0], [...cmd.slice(1), ...args], {
      encoding: "utf8",
      timeout: 30000,
    });
    if (r.error) {
      const code = (r.error as NodeJS.ErrnoException).code;
      if (code === "ENOENT") continue; // 该候选不存在，试下一个
      return { ok: false, output: `执行 zcode 失败: ${r.error.message}`, code: 1 };
    }
    const output = [r.stdout, r.stderr].filter(Boolean).join("\n").trim();
    return { ok: r.status === 0, output, code: r.status ?? 1 };
  }
  return {
    ok: false,
    output: "未找到 zcode CLI。请先安装：bash scripts/install.sh（或 pip install -e adapters）",
    code: 127,
  };
}
```

- [ ] 冒烟：本机 `.venv/bin/zcode` 已装——`node -e "const m=await import('...zcode.ts'); console.log(m.runZcode(['version']))"` 输出 `ok:true` 且含 `zcode 0.3.8`
- [ ] commit

---

## Task 3 — index.ts：/zcode 命令透传

**Files**
- Create `adapters/platforms/pi/extension/index.ts`

**Interfaces**
- Consumes: `runZcode`
- Produces: `export default function (pi: ExtensionAPI): void`

**步骤**

- [ ] 实现：

```typescript
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { runZcode } from "./zcode";

export default function (pi: ExtensionAPI) {
  pi.registerCommand("zcode", {
    description: "调用 zcode 子命令（如 /zcode skills list、/zcode ticket context）",
    handler: async (args, ctx) => {
      const argv = args ? args.trim().split(/\s+/) : [];
      const r = runZcode(argv);
      if (!r.ok) {
        ctx.ui.notify(r.output || "zcode 命令失败", "error");
        return;
      }
      ctx.ui.setWidget("zcode", r.output.split("\n"));
    },
  });
}
```

- [ ] 冒烟：`pi -e adapters/platforms/pi/extension/index.ts`，输入 `/zcode skills list` → 编辑区上方 widget 显示技能清单；`/zcode version` → 显示 `zcode 0.3.8`
- [ ] commit

---

## Task 4 — index.ts：zcode_* 只读工具注册

**Files**
- Modify `adapters/platforms/pi/extension/index.ts`

**Interfaces**
- Consumes: `runZcode`、`Type`（typebox）
- Produces: 4 个工具 `zcode_ticket_context` / `zcode_memory_search` / `zcode_skills_list` / `zcode_glossary`

**步骤**

- [ ] 在 Task 3 的 factory 内追加：

```typescript
import { Type } from "typebox";

// factory 内：
pi.registerTool({
  name: "zcode_ticket_context",
  label: "Zcode 工单状态",
  description: "查看当前仓库工单工作台状态（只读）：Phase、当前工单、阻塞项",
  parameters: Type.Object({}),
  async execute() {
    const r = runZcode(["ticket", "context"]);
    return { content: [{ type: "text", text: r.output }], details: {} };
  },
});

pi.registerTool({
  name: "zcode_memory_search",
  label: "检索记忆",
  description: "检索 zcode 跨会话语义记忆（只读）",
  parameters: Type.Object({ query: Type.String({ description: "查询文本" }) }),
  async execute(_id, params) {
    const r = runZcode(["memory", "search", params.query]);
    return { content: [{ type: "text", text: r.output }], details: {} };
  },
});

pi.registerTool({
  name: "zcode_skills_list",
  label: "技能清单",
  description: "列出 zcode 技能库可用技能（只读）",
  parameters: Type.Object({}),
  async execute() {
    const r = runZcode(["skills", "list"]);
    return { content: [{ type: "text", text: r.output }], details: {} };
  },
});

pi.registerTool({
  name: "zcode_glossary",
  label: "术语表",
  description: "查询 zcode 项目术语表（只读）",
  parameters: Type.Object({}),
  async execute() {
    const r = runZcode(["ticket", "gloss"]);
    return { content: [{ type: "text", text: r.output }], details: {} };
  },
});
```

- [ ] 冒烟：`pi -e ...` 后让模型调用 `zcode_ticket_context`（在本仓库目录）→ 返回工单状态摘要；或 `pi --list-tools` 类命令确认 4 工具已注册
- [ ] commit

---

## Task 5 — Pi Package 打包 + INSTALL.md

**Files**
- Modify `package.json`（根）
- Modify `adapters/platforms/pi/INSTALL.md`

**步骤**

- [ ] 根 `package.json` 的 `keywords` 追加 `"pi-package"`，并新增 `pi` 键：

```json
"keywords": ["skills", "agent", "llm", "local-model", "zcode", "pi-package"],
"pi": {
  "extensions": ["./adapters/platforms/pi/extension"],
  "skills": ["./skills"]
}
```

- [ ] INSTALL.md 追加「深度插件」小节：`pi install <本仓库路径>` 或 `pi install git:github.com/zenocode01/Zcode.git` 装齐 skills + extension；卸载 `pi remove ...`；zcode CLI 需先 `bash scripts/install.sh` 安装
- [ ] 冒烟：`pi install /home/zeno/ZENO/Zcode/Zcode-0.0`（或 `pi -e` 验证 package 识别 skills+extensions）；`pi list` 可见 zcode
- [ ] commit

---

## Task 6 — 文档同步 + 收尾

**Files**
- Modify `README.md`（平台支持表 pi 行加"深度插件"；目录结构补 `adapters/platforms/pi/extension`）
- Modify `AGENTS.md`（当前状态补 pi 插件）
- Modify `docs/UBIQUITOUS_LANGUAGE.md`（新术语：pi 插件 / 命令透传，用 `zcode ticket gloss add`）

**步骤**

- [ ] `zcode ticket gloss add 命令透传 <定义>`、`pi 插件 <定义>` 两词条
- [ ] README / AGENTS 同步
- [ ] `zcode ticket phase review --green`；`zcode ticket transition T-027 review`；`zcode ticket resolve T-027 "..."`；`zcode ticket close T-027`

## 自审

- 规格覆盖：spec 3.1 命令透传 → Task 3；3.2 工具注册 → Task 4；3.3 package 打包 → Task 5；第 5 节安全 → Global Constraints 1/2。全对齐。
- 占位符：无。
- 类型一致：`ZcodeResult` 在 Task 1 定义，Task 2 实现、Task 3/4 引用，字段 `ok/output/code` 一致，无漂移。
