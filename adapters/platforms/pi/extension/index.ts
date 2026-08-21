// Zcode 的 pi-agent 深度插件入口。
// 三合一：
//   1. /zcode <子命令> 命令透传（人用）
//   2. zcode_* 只读工具（AI 用，无副作用）
//   3. 由根 package.json 的 pi 键打包为 Pi Package（分发用）
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { runZcode } from "./zcode";

export default function (pi: ExtensionAPI) {
  // ---- 1. 命令透传（人用） ----
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

  // ---- 2. 只读工具（AI 用） ----
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
}
