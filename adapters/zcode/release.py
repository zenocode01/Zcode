"""zcode release — 版本迭代命令（T-028）。

一次完成：统一 bump 五处版本号 → 归并 CHANGELOG「未发布」条目 → 打 git tag → 可选推送。
设计：
- `__version__`（adapters/zcode/__init__.py）为版本真相，其余 4 处由本模块统一写入
- CHANGELOG 版本 = 发布版本：close 时条目写入「未发布」区块，release 时归并为正式版本
- 每步失败即停，报告已完成步骤
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# 需要统一写入版本号的文件：(路径, 匹配正则, 替换模板)
VERSION_FILES: list[tuple[Path, str, str]] = [
    (REPO_ROOT / "adapters" / "zcode" / "__init__.py",
     r'__version__ = "[^"]+"', '__version__ = "{}"'),
    (REPO_ROOT / "adapters" / "pyproject.toml",
     r'^version = "[^"]+"', 'version = "{}"'),
    (REPO_ROOT / "package.json",
     r'"version": "[^"]+"', '"version": "{}"'),
    (REPO_ROOT / "marketplace.json",
     r'"version": "[^"]+"', '"version": "{}"'),
    (REPO_ROOT / ".claude-plugin" / "plugin.json",
     r'"version": "[^"]+"', '"version": "{}"'),
]

CHANGELOG = REPO_ROOT / "CHANGELOG.md"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
BLOCK_RE = re.compile(r"^## \[([^\]]+)\](.*)$")


class ReleaseError(Exception):
    """release 失败（打印后返回非 0）。"""


def current_version() -> str:
    """读 __init__.py 的 __version__（版本真相）。"""
    f = REPO_ROOT / "adapters" / "zcode" / "__init__.py"
    text = f.read_text(encoding="utf-8")
    m = re.search(r'__version__ = "([^"]+)"', text)
    if not m:
        raise ReleaseError("找不到 __version__（adapters/zcode/__init__.py）")
    return m.group(1)


def _version_parts(v: str) -> list[int]:
    parts = [int(x) for x in v.split(".")]
    if len(parts) != 3:
        raise ReleaseError(f"版本号格式非法（需 X.Y.Z）: {v}")
    return parts


def bump_version(current: str, kind: str) -> str:
    """按 patch/minor/major 递增，或手动 X.Y.Z（须 > current）。"""
    if kind in ("patch", "minor", "major"):
        a, b, c = _version_parts(current)
        if kind == "patch":
            return f"{a}.{b}.{c + 1}"
        if kind == "minor":
            return f"{a}.{b + 1}.0"
        return f"{a + 1}.0.0"
    if VERSION_RE.match(kind):
        if _version_parts(kind) <= _version_parts(current):
            raise ReleaseError(f"新版本 {kind} 必须大于当前版本 {current}")
        return kind
    raise ReleaseError(f"非法 bump 类型: {kind}（可用 patch/minor/major/X.Y.Z）")


def write_version_files(version: str) -> list[Path]:
    """统一写入五处版本号，返回实际修改的文件列表。"""
    changed: list[Path] = []
    for path, pattern, template in VERSION_FILES:
        text = path.read_text(encoding="utf-8")
        new_text, n = re.subn(pattern, template.format(version), text, count=1, flags=re.MULTILINE)
        if n == 0:
            raise ReleaseError(f"未能在 {path} 找到版本号（pattern: {pattern}）")
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed.append(path)
    return changed


def _parse_blocks(content: str) -> list[tuple[str, str, str]]:
    """把 CHANGELOG 拆成 [(完整 header 行, tag, body)]。tag 是版本号或「未发布」。"""
    lines = content.splitlines()
    blocks: list[tuple[str, str, str]] = []
    cur_header: str | None = None
    cur_tag = ""
    cur_body: list[str] = []
    for line in lines:
        m = BLOCK_RE.match(line)
        if m and line.startswith("## ["):
            if cur_header is not None:
                blocks.append((cur_header, cur_tag, "\n".join(cur_body).strip()))
            cur_header = line
            cur_tag = m.group(1)
            cur_body = []
        else:
            if cur_header is not None:
                cur_body.append(line)
    if cur_header is not None:
        blocks.append((cur_header, cur_tag, "\n".join(cur_body).strip()))
    return blocks


def collect_unreleased(content: str, current: str) -> str:
    """收集「未发布」条目：未发布区块 + 所有版本 > current 的区块内容。"""
    bodies: list[str] = []
    for _, tag, body in _parse_blocks(content):
        if not body:
            continue
        if tag == "未发布":
            bodies.append(body)
        elif VERSION_RE.match(tag) and _version_parts(tag) > _version_parts(current):
            bodies.append(body)
    return "\n\n".join(bodies)


def rebuild_changelog(content: str, new_version: str, current: str) -> str:
    """重建 CHANGELOG：头部 + 新版本区块（归并未发布）+ 保留 <= current 的区块。"""
    # 头部 = 第一个 ## [ 之前的内容
    head_m = re.search(r"^## \[", content, re.MULTILINE)
    head = content[: head_m.start()] if head_m else content

    unreleased = collect_unreleased(content, current)
    date = datetime.now().strftime("%Y-%m-%d")
    new_block = f"## [{new_version}] - {date}\n\n" + (unreleased if unreleased else "（无变更记录）")

    kept: list[tuple[str, str]] = []
    for header, tag, body in _parse_blocks(content):
        if tag == "未发布":
            continue  # 归并后丢弃
        if VERSION_RE.match(tag) and _version_parts(tag) > _version_parts(current):
            continue  # 归并后丢弃
        kept.append((header, body))

    parts = [head.rstrip()]
    parts.append(new_block)
    for header, body in kept:
        parts.append(header + ("\n" + body if body else ""))
    return "\n\n".join(p for p in parts if p).rstrip() + "\n"


def _run(cmd: list[str]) -> tuple[int, list[str]]:
    r = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    return r.returncode, (r.stdout or "").splitlines() + (r.stderr or "").splitlines()


def precheck() -> str | None:
    """返回拒绝原因（None = 可 release）。"""
    if not (REPO_ROOT / ".git").exists():
        return "不是 git 仓库"
    code, out = _run(["git", "status", "--porcelain"])
    if code != 0:
        return "git status 失败"
    if out:
        return "工作区有未提交改动，先提交或 stash 再 release: " + ", ".join(
            l[3:].strip() for l in out if len(l) >= 4
        )[:200]
    return None


def run_release(kind: str = "patch", dry_run: bool = False, push: bool = False) -> int:
    """执行 release。返回退出码。"""
    cur = current_version()
    new = bump_version(cur, kind)

    if dry_run:
        print(f"== zcode release --dry-run（当前 {cur} → {new}）==")
        print(f"  [1] 统一写版本号到 {len(VERSION_FILES)} 处")
        print(f"  [2] 归并 CHANGELOG 未发布条目 → ## [{new}]")
        print(f"  [3] git add + commit（release v{new}）")
        print(f"  [4] git tag v{new}")
        if push:
            print(f"  [5] git push origin HEAD --tags")
        print("== 完成（dry-run，未执行）==")
        return 0

    reason = precheck()
    if reason:
        raise ReleaseError(reason)

    # 1. 写版本号
    changed = write_version_files(new)
    print(f"→ 版本号 {cur} → {new}（{len(changed)} 个文件）")

    # 2. CHANGELOG 归并
    content = CHANGELOG.read_text(encoding="utf-8") if CHANGELOG.exists() else "# Changelog\n"
    new_content = rebuild_changelog(content, new, cur)
    CHANGELOG.write_text(new_content, encoding="utf-8")
    print(f"→ CHANGELOG 已归并为 ## [{new}]")

    # 3. commit（绕过 hook：release 是版本管理元操作，不受工作台 Phase 约束）
    _run(["git", "add", "-A"])
    code, out = _run(["git", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", f"release v{new}"])
    if code != 0:
        raise ReleaseError(f"git commit 失败: " + "\n".join(out[-5:]))

    # 4. tag
    code, out = _run(["git", "tag", f"v{new}"])
    if code != 0:
        raise ReleaseError(f"git tag 失败: " + "\n".join(out[-5:]))

    # 5. 可选推送
    if push:
        code, out = _run(["git", "push", "origin", "HEAD", "--tags"])
        if code != 0:
            raise ReleaseError(f"git push 失败: " + "\n".join(out[-5:]))

    print(f"✓ 已发布 v{new}（tag v{new}" + ("，已推送" if push else "，未推送") + "）")
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="zcode release", description="版本迭代：统一 bump 版本号 + 归并 CHANGELOG + 打 tag")
    parser.add_argument("kind", nargs="?", default="patch",
                        help="patch / minor / major / X.Y.Z（默认 patch）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划不执行")
    parser.add_argument("--push", action="store_true", help="推送 origin 与 tag")
    args = parser.parse_args(argv)
    try:
        return run_release(args.kind, dry_run=args.dry_run, push=args.push)
    except ReleaseError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
