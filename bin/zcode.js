#!/usr/bin/env node
// Zcode CLI npm 入口：调用 Python 端的 zcode 命令
// 技术栈决策：Python（适配层/编排）+ npm 分发（CLI 入口）
const { spawnSync } = require("node:child_process");

const args = process.argv.slice(2);
const result = spawnSync("python3", ["-m", "zcode", ...args], { stdio: "inherit" });

if (result.error) {
  console.error("无法运行 python3 -m zcode。请先安装 Python 适配层：");
  console.error("  cd adapters && pip install -e .");
  process.exit(1);
}
process.exit(result.status ?? 1);
