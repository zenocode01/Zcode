"""zcode update — 自更新命令（T-025）。

从仓库 git 远程拉取最新代码，刷新 Python 包 / npm 链接 / 技能与钩子。
设计：
- 前置检查（工作区干净）→ git fetch 对比 → pull --ff-only → pip install -e →
  npm link（可选）→ scripts/install.sh → 变更摘要
- 每步失败即停，报告已完成步骤与手动处理提示；--dry-run 只打印计划不执行。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# 仓库根 = adapters/zcode/update.py 上溯三级
REPO_ROOT = Path(__file__).resolve().parents[2]


class UpdateError(Exception):
    """更新失败（打印后返回非 0）。"""


def _run(cmd: list[str], cwd: Path) -> tuple[int, list[str]]:
    """执行命令，返回 (退出码, stdout 行)。"""
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return r.returncode, (r.stdout or "").splitlines()


def precheck(root: Path) -> str | None:
    """返回拒绝原因（None = 可更新）。"""
    if not (root / ".git").exists():
        return "不是 git 仓库（缺 .git），无法自更新"
    code, out = _run(["git", "status", "--porcelain"], root)
    if code != 0:
        return "git status 失败"
    if out:
        return "工作区有未提交改动，先提交或 stash 再更新（更新会拉取覆盖本地代码）: " + ", ".join(
            l[3:].strip() for l in out if len(l) >= 4
        )[:200]
    return None


def plan(root: Path) -> list[tuple[str, list[str], bool]]:
    """返回步骤列表 (描述, 命令, 是否关键)。npm/install.sh 按存在性动态包含。"""
    steps: list[tuple[str, list[str], bool]] = [
        ("git fetch origin（获取远程更新）", ["git", "fetch", "origin"], True),
        ("git pull --ff-only（快进合并到 main）", ["git", "pull", "--ff-only"], True),
        ("pip install -e adapters（刷新 Python 包/依赖）",
         [sys.executable, "-m", "pip", "install", "-e", "adapters"], True),
    ]
    if (root / "package.json").exists():
        steps.append(("npm link（刷新全局命令，失败仅警告）", ["npm", "link"], False))
    if (root / "scripts" / "install.sh").exists():
        steps.append(("bash scripts/install.sh（刷新技能软链/CLI 包装器/钩子）",
                      ["bash", "scripts", "install.sh"], True))
    return steps


def run_update(dry_run: bool = False, root: Path | None = None) -> int:
    """执行更新。返回进程退出码。"""
    root = root or REPO_ROOT
    steps = plan(root)

    if dry_run:
        print("== zcode update --dry-run（只打印计划，不执行）==")
        for i, (desc, _, _) in enumerate(steps, 1):
            print(f"  [{i}/{len(steps)}] {desc}")
        print("== 完成（dry-run）==")
        return 0

    reason = precheck(root)
    if reason:
        raise UpdateError(reason)

    # 1. fetch（失败即停，附网络/凭据提示）
    print("→ git fetch origin（获取远程更新）")
    code, out = _run(["git", "fetch", "origin"], root)
    if code != 0:
        detail = "\n".join(out[-3:]) if out else ""
        raise UpdateError(
            f"git fetch 失败（检查网络/凭据）{(' — ' + detail) if detail else ''}\n"
            f"处理: 网络问题重试；凭据问题见 zcode memory search 'git push 认证'"
        )

    # 2. 已最新？（fetch 后无新提交 → 直接退出，避免无更新全量重装）
    code, out = _run(["git", "rev-list", "--count", "HEAD..origin/main"], root)
    if code == 0 and out and out[0].strip() == "0":
        print("✓ 已是最新版本（origin/main 无新提交）")
        return 0

    # 3. 其余步骤（pull / pip / npm / install.sh）
    done: list[str] = ["git fetch origin"]
    for desc, cmd, critical in steps[1:]:
        print(f"→ {desc}")
        code, out = _run(cmd, root)
        if code != 0:
            detail = "\n".join(out[-3:]) if out else ""
            hint = "（可选步骤，已跳过）" if not critical else ""
            raise UpdateError(
                f"步骤失败: {desc}{hint}\n  exit {code}{(' — ' + detail) if detail else ''}\n"
                f"已完成: {', '.join(done) if done else '无'}\n"
                f"处理: 手动执行失败命令排查后重跑 zcode update"
            )
        done.append(desc)

    # 变更摘要（fetch 后的新提交）
    code, out = _run(["git", "log", "--oneline", "-8"], root)
    if code == 0 and out:
        print("最近提交:")
        for line in out:
            print(f"  {line}")
    print("✓ zcode 已更新（运行 zcode version 查看版本）")
    return 0
