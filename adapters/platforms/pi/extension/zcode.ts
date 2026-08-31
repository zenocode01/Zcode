// zcode CLI 定位与执行助手。
// 三级候选定位 zcode：PATH 中的 zcode → ~/.local/bin/zcode → python3 -m zcode。
// 任一候选 ENOENT（命令不存在）则试下一个；命令存在则返回其退出码与合并输出。
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
