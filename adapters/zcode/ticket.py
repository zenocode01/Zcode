"""工单驱动开发工作台（Layer 2）——移植自 vibe-workbench 的双状态机 + 可执行强制。

两个状态机:
- Agent 阶段机（运行时）: analyze → plan → implement → verify → review → commit
- 工单生命周期机（持久化）: backlog → in-progress → review → done / blocked → backlog

核心原则:
- 所有状态变更走命令，脚本校验守卫（guard），不手动改锚点行
- STATUS.md 由命令自动刷新；validate / pre-commit 拦截过期与非法提交
- Markdown 机器可读锚点（Phase:/Status:/Depends:/Resolution:/Domain:...）为唯一事实来源

与 vibe-workbench 兼容：文件格式（tickets.md / docs/CONTEXT.md / STATUS.md /
docs/UBIQUITOUS_LANGUAGE.md / .vibe/）与 ~/.vibe/projects.json 注册表完全一致，
两个 CLI 可混用；STATUS.md 保鲜判定对生成器注释与行尾做归一化。
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

VALID_PHASES = ("analyze", "plan", "implement", "verify", "review", "commit")
VALID_STATES = ("backlog", "in-progress", "review", "done", "blocked")
TICKET_TRANSITIONS = {
    "backlog": ["in-progress"],
    "in-progress": ["review", "blocked"],
    "review": ["in-progress", "done"],
    "blocked": ["backlog"],
    "done": [],
}
PHASE_TRANSITIONS = {
    "analyze": ["plan"],
    "plan": ["implement"],
    "implement": ["verify"],
    "verify": ["review", "implement"],
    "review": ["commit", "implement"],
    "commit": [],
}
# 状态/元文件前缀：工作区脏判定时这些文件的改动不算源码改动
# （状态文件 + 仓库级文档 README/AGENTS/CHANGELOG/docs：随工单提交，不阻塞 begin 自动开分支）
STATE_PREFIXES = (
    "tickets.md", "docs/CONTEXT.md", "docs/UBIQUITOUS_LANGUAGE.md",
    "STATUS.md", "docs/ADR/", ".vibe/",
    "README.md", "CHANGELOG.md", "AGENTS.md", "docs/",
)
VERIFY_ARTIFACT_PATTERNS = (
    "test_*.py", "*_test.py", "*.test.js", "*.test.ts", "*.spec.js", "*.spec.ts",
    "*_test.go", "*.test.rb", "test_*.rb", "*.test.dart", "*.spec.dart", "*.test.exs",
    "Test*.java", "*Test.java", "tests", "test", "__tests__", "spec",
)

REGISTRY = Path.home() / ".vibe" / "projects.json"
TEMPLATE_DIR = Path(__file__).parent / "templates" / "ticket"


class TicketError(Exception):
    """命令执行错误（守卫失败 / 非法流转等），打印后返回非 0。"""


# ---------- 基础 IO ----------
def read_text(file: Path) -> str | None:
    if not file.exists():
        return None
    return file.read_text(encoding="utf-8")


def write_text(file: Path, content: str) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8")


def read_lines(file: Path) -> list[str]:
    content = read_text(file)
    if content is None:
        return []
    return content.replace("\r\n", "\n").split("\n")


def get_anchor(file: Path, anchor: str) -> str | None:
    for line in read_lines(file):
        m = re.match(r"^" + re.escape(anchor) + r": *([^\r\n]*)\r?$", line)
        if m:
            return m.group(1).strip()
    return None


def set_anchor(file: Path, anchor: str, value: str) -> bool:
    content = read_text(file)
    if content is None:
        raise TicketError(f"找不到 {file}")
    pattern = r"(?m)^" + re.escape(anchor) + r": *[^\r\n]*\r?$"
    replacement = f"{anchor}: {value}"
    if re.search(pattern, content):
        write_text(file, re.sub(pattern, replacement, content))
        return True
    return False


# ---------- git 封装 ----------
def run_git(root: Path, args: list[str]) -> tuple[int, list[str]]:
    r = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, errors="replace",
    )
    out = (r.stdout or "").splitlines()
    if r.returncode != 0 and r.stderr:
        out.extend((r.stderr or "").splitlines())
    return r.returncode, out


def git_output(root: Path, args: list[str]) -> str:
    _, out = run_git(root, args)
    return out[0].strip() if out else ""


# ---------- 模板定位 ----------
def template_dir() -> Path:
    env = __import__("os").environ.get("ZCODE_TICKET_TEMPLATE")
    if env and Path(env).is_dir():
        return Path(env)
    return TEMPLATE_DIR


# ---------- 工单解析 ----------
@dataclass
class Ticket:
    id: str
    title: str
    status: str | None = None
    depends: list[str] = field(default_factory=list)
    resolution: str | None = None
    block: list[str] = field(default_factory=list)

    def block_text(self) -> str:
        return "\n".join(self.block)


def strip_inline_comment(value: str) -> str:
    return re.sub(r"\s*#.*$", "", value).strip()


def parse_tickets(file: Path) -> list[Ticket]:
    tickets: list[Ticket] = []
    current: Ticket | None = None
    block: list[str] = []
    in_fence = False
    for line in read_lines(file):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^##\s+(T-\d+)(?:\s+(.*))?$", line)
        if m:
            if current:
                current.block = block
                tickets.append(current)
            block = []
            current = Ticket(id=m.group(1), title=(m.group(2) or "").strip())
        if current:
            block.append(line)
            if line.startswith("Status:"):
                current.status = strip_inline_comment(line[len("Status:"):])
            elif line.startswith("Depends:"):
                dep_str = strip_inline_comment(line[len("Depends:"):])
                current.depends = [d.strip() for d in re.split(r"[,;]", dep_str) if d.strip()]
            elif line.startswith("Resolution:"):
                current.resolution = strip_inline_comment(line[len("Resolution:"):])
    if current:
        current.block = block
        tickets.append(current)
    return tickets


def get_ticket(file: Path, tid: str) -> Ticket | None:
    for t in parse_tickets(file):
        if t.id == tid:
            return t
    return None


def set_ticket_status(file: Path, tid: str, new_status: str) -> bool:
    lines = read_lines(file)
    out: list[str] = []
    in_block = False
    changed = False
    for line in lines:
        m = re.match(r"^##\s+(T-\d+)\s*", line)
        if m:
            in_block = m.group(1) == tid
        if in_block and line.startswith("Status:"):
            out.append(f"Status: {new_status}")
            changed = True
            continue
        out.append(line)
    if changed:
        write_text(file, "\n".join(out))
    return changed


def set_ticket_anchor(file: Path, tid: str, anchor: str, value: str) -> bool:
    """在指定工单块内设置/新增一行锚点（如 Resolution:）。"""
    lines = read_lines(file)
    out: list[str] = []
    in_block = False
    found = False
    replaced = False
    header_idx = -1
    for line in lines:
        m = re.match(r"^##\s+(T-\d+)\s*", line)
        if m:
            in_block = m.group(1) == tid
            if in_block:
                found = True
                header_idx = len(out)
        if in_block and line.startswith(anchor + ":"):
            out.append(f"{anchor}: {value}")
            replaced = True
            continue
        out.append(line)
    if not found:
        raise TicketError(f"工单 {tid} 不存在于 {file}")
    if not replaced:
        out.insert(header_idx + 1, f"{anchor}: {value}")
    write_text(file, "\n".join(out))
    return True


# ---------- 术语表解析 ----------
def parse_glossary(file: Path) -> list[dict]:
    entries: list[dict] = []
    current: dict | None = None
    in_fence = False
    for line in read_lines(file):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current:
                entries.append(current)
            current = {"term": m.group(1).strip(), "definition": None}
        elif current:
            m2 = re.match(r"^-\s*\*\*含义\*\*[：:]\s*(.+)$", line)
            if m2:
                current["definition"] = m2.group(1).strip()
    if current:
        entries.append(current)
    return entries


# ---------- 日志 / meta / 注册表 ----------
def add_log(root: Path, event: str, detail: str) -> None:
    log_dir = root / ".vibe"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "log.md"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {event} | {detail}\n")


def get_meta(root: Path, key: str) -> str | None:
    return get_anchor(root / ".vibe" / "vibe.meta", key)


def set_meta(root: Path, key: str, value: str) -> None:
    meta = root / ".vibe" / "vibe.meta"
    if not meta.exists():
        write_text(meta, "")
    if not set_anchor(meta, key, value):
        write_text(meta, (read_text(meta) or "") + f"{key}: {value}\n")


def get_registry() -> list[dict]:
    if not REGISTRY.exists():
        return []
    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "value" in data:
            return data["value"]
        return [data]
    except (json.JSONDecodeError, OSError):
        return []


def save_registry(items: list[dict]) -> None:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def register_project(path: str) -> None:
    reg = get_registry()
    if not any(e.get("path") == path for e in reg):
        reg.append({"name": Path(path).name, "path": path})
        save_registry(reg)


# ---------- 依赖 / 环检测 ----------
def deps_done(by_id: dict[str, Ticket], deps: list[str]) -> bool:
    return all(by_id.get(d) and by_id[d].status == "done" for d in deps)


def dep_cycle(tickets: list[Ticket]) -> bool:
    """Kahn 拓扑排序；有剩余节点即存在依赖环。"""
    by_id = {t.id: t for t in tickets}
    indegree = {t.id: sum(1 for d in t.depends if d in by_id) for t in tickets}
    queue = [t.id for t in tickets if indegree[t.id] == 0]
    processed = 0
    while queue:
        tid = queue.pop(0)
        processed += 1
        for t in tickets:
            if tid in t.depends:
                indegree[t.id] -= 1
                if indegree[t.id] == 0:
                    queue.append(t.id)
    return processed < len(tickets)


# ---------- 分支 / 工作区 ----------
def branch_mode(ctx_file: Path) -> str:
    m = get_anchor(ctx_file, "BranchMode")
    return (m or "auto").lower()


def repo_clean(root: Path) -> bool:
    _, out = run_git(root, ["status", "--porcelain"])
    for line in out:
        if len(line) < 4:
            continue
        p = line[3:].strip()
        if not any(p.startswith(s) for s in STATE_PREFIXES):
            return False
    return True


def repo_has_commit(root: Path) -> bool:
    code, _ = run_git(root, ["rev-parse", "--verify", "HEAD"])
    return code == 0


def ticket_committed(root: Path, tid: str) -> bool:
    code, out = run_git(root, ["log", "--oneline", "--grep=" + tid, "-1"])
    return code == 0 and len(out) > 0


def find_repo_root() -> Path | None:
    """向上找含 tickets.md 的目录（工作台根）。"""
    p = Path.cwd()
    while True:
        if (p / "tickets.md").exists():
            return p
        if p.parent == p:
            return None
        p = p.parent


# ---------- 状态机定义 ----------
def phase_legal(frm: str, to: str) -> bool:
    if to == "analyze":
        return True  # 任意阶段可回 analyze（需求变化）
    if frm == to:
        return True
    return to in PHASE_TRANSITIONS.get(frm, [])


def ticket_legal(frm: str, to: str) -> bool:
    return to in TICKET_TRANSITIONS.get(frm, [])


def has_verify_artifacts(root: Path) -> bool:
    for pattern in VERIFY_ARTIFACT_PATTERNS:
        try:
            if next(root.rglob(pattern), None):
                return True
        except PermissionError:
            continue
    return False


def phase_guard(frm: str, to: str, root: Path, flags: list[str]) -> bool:
    ctx_file = root / "docs/CONTEXT.md"
    tickets_file = root / "tickets.md"
    transition = f"{frm}->{to}"
    if transition == "analyze->plan":
        if not get_anchor(ctx_file, "Domain"):
            print("守卫失败: analyze→plan 需要 docs/CONTEXT.md 的 Domain: 非空（记录你对项目的领域理解）")
            return False
    elif transition == "plan->implement":
        if not tickets_file.exists():
            print("守卫失败: plan→implement 需要 tickets.md 已存在")
            return False
    elif transition == "implement->verify":
        if not has_verify_artifacts(root):
            print("守卫失败: implement→verify 需要存在验证产物（测试文件），用 --force 绕过")
            return "--force" in flags
    elif transition == "verify->review":
        if "--green" not in flags:
            print("守卫失败: verify→review 需要 --green（验证绿）")
            return False
    elif transition == "verify->implement":
        if "--red" not in flags:
            print("守卫失败: verify→implement 需要 --red（验证红）")
            return False
    elif transition == "review->commit":
        if "--pass" not in flags:
            print("守卫失败: review→commit 需要 --pass（审查通过）")
            return False
    elif transition == "review->implement":
        if "--reject" not in flags:
            print("守卫失败: review→implement 需要 --reject（审查打回）")
            return False
    return True


def verify_evidence(root: Path, frm: str, to: str, cmd: str) -> None:
    """配了 TestCommand 就真实执行并记录；失败方向与预期不符则拒绝。"""
    ev_dir = root / ".vibe" / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    ev_file = ev_dir / f"{stamp}-{frm}-{to}.txt"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, errors="replace")
    text = (f"command: {cmd}\nexit: {r.returncode}\n--- output ---\n"
            + (r.stdout or "") + (r.stderr or ""))
    write_text(ev_file, text)
    add_log(root, "verify", f"{frm} -> {to} exit={r.returncode} [{cmd}] 证据: {ev_file}")
    if to == "review" and r.returncode != 0:
        raise TicketError(f"TestCommand 运行失败 (exit {r.returncode})，verify→review 被拒（证据: {ev_file}）")
    if to == "implement" and r.returncode == 0:
        raise TicketError(f"TestCommand 运行通过 (exit 0)，verify→implement --red 被拒（证据: {ev_file}）")


# ---------- STATUS.md 生成器（status / validate / check-commit 共用，保鲜判定一致） ----------
def status_content(root: Path) -> str:
    ctx_file = root / "docs/CONTEXT.md"
    tickets_file = root / "tickets.md"
    gloss_file = root / "docs/UBIQUITOUS_LANGUAGE.md"
    phase = get_anchor(ctx_file, "Phase") or ""
    cur = get_anchor(ctx_file, "Current Ticket") or ""
    domain = get_anchor(ctx_file, "Domain") or ""
    test_cmd = get_anchor(ctx_file, "TestCommand") or ""
    branch = get_anchor(ctx_file, "BranchMode") or "auto"
    tickets = parse_tickets(tickets_file)
    gloss_count = len(parse_glossary(gloss_file))

    if len(domain) > 80:
        domain = domain[:80] + "…"
    if not domain:
        domain = "(未填写)"
    if not test_cmd:
        test_cmd = "(未配置)"

    lines = [
        "# STATUS — 当前状态总览",
        "",
        "> 由 zcode ticket status 自动生成，请勿手写。Agent 先读本文件即可了解全貌；细节按需再读对应文件。",
        "",
        "## 关键状态",
        f"Phase: {phase}",
        f"Current Ticket: {cur}",
        f"Domain: {domain}",
        f"TestCommand: {test_cmd}",
        f"BranchMode: {branch}",
        f"术语表: {gloss_count} 条 (docs/UBIQUITOUS_LANGUAGE.md)",
        "",
    ]
    cur_ticket = get_ticket(tickets_file, cur) if cur else None
    if cur_ticket:
        lines.append(f"## 当前工单 {cur_ticket.id} ({cur_ticket.title}) [{cur_ticket.status}]")
        lines.append(cur_ticket.block_text())
        lines.append("")
    lines.append("## 工单")
    if not tickets:
        lines.append("(无)")
    else:
        for t in tickets:
            box = "[x]" if t.status == "done" else "[ ]"
            dep = f"  (depends: {', '.join(t.depends)})" if t.depends else ""
            res = "  ✓已记录修复" if t.resolution else ""
            lines.append(f"- {box} **{t.id}** {t.title} — {t.status}{dep}{res}")
    lines.append("")
    lines.append("## 阻塞")
    blocked = [t for t in tickets if t.status == "blocked"]
    if blocked:
        for t in blocked:
            lines.append(f"- **{t.id}** {t.title}")
    else:
        lines.append("(无)")
    lines.append("")
    lines.append("<!-- GENERATED-BY-ZCODE -->")
    return "\n".join(lines)


def _status_normalized(text: str) -> str:
    """保鲜判定归一化：行尾 + 生成器注释 + 首尾换行（vibe/zcode 混用兼容）。"""
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"<!-- GENERATED-BY-[A-Z-]+ -->", "<!-- GENERATED-BY-* -->", text)
    return text.strip("\n")


def status_fresh(root: Path) -> bool:
    status_file = root / "STATUS.md"
    if not status_file.exists():
        return False
    return _status_normalized(read_text(status_file) or "") == _status_normalized(status_content(root))


# ---------- 命令实现 ----------
def _copy_missing(src: Path, dst: Path, skipped: list[str]) -> None:
    """递归复制模板：已存在的文件跳过，目录递归合并（不覆盖任何已有文件）。"""
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            if not target.exists():
                shutil.copytree(item, target)
            else:
                _copy_missing(item, target, skipped)
        else:
            if target.exists():
                skipped.append(str(target.relative_to(dst.parent)))
            else:
                shutil.copy2(item, target)


def cmd_init(args: list[str]) -> None:
    if len(args) < 1:
        raise TicketError("用法: zcode ticket init <project> 或 zcode ticket init .（当前目录）[--existing]")
    existing = "--existing" in args
    positional = [a for a in args if not a.startswith("--")]
    if len(positional) < 1:
        raise TicketError("用法: zcode ticket init <project> 或 zcode ticket init .（当前目录）[--existing]")
    target = positional[0]
    if target == ".":
        dest = Path.cwd()
    elif Path(target).is_absolute():
        dest = Path(target)
    else:
        dest = Path.cwd() / target
    dest.mkdir(parents=True, exist_ok=True)

    template = template_dir()
    if not template.is_dir():
        raise TicketError(f"找不到工作台模板: {template}（设置 ZCODE_TICKET_TEMPLATE 可覆盖）")

    if any(dest.iterdir()):
        if not existing:
            raise TicketError(f"目录非空，拒绝覆盖: {dest}（在已有项目上启用请加 --existing，只补缺失文件不覆盖）")
        skipped: list[str] = []
        _copy_missing(template, dest, skipped)
        if skipped:
            print(f"已跳过 {len(skipped)} 个已存在文件（不覆盖）；只新增缺失文件: {', '.join(sorted(set(skipped)))}")
    else:
        _copy_missing(template, dest, [])

    meta_text = "\n".join([
        f"project: {dest.name}",
        f"created: {datetime.now().strftime('%Y-%m-%d')}",
        "workbench: zcode",
        "branch: ",
        "branch-base: ",
    ]) + "\n"
    write_text(dest / ".vibe" / "vibe.meta", meta_text)

    if not (dest / ".git").exists():
        run_git(dest, ["init", "--quiet"])
        print("已 git init")
    cmd_install([dest], quiet_root=dest)
    register_project(str(dest))
    add_log(dest, "init", "zcode 工单工作台初始化")
    cmd_status(["-q"], root=dest)
    print(f"✓ 工单工作台已就绪: {dest}")
    print(f"  已登记到项目注册表 (~/.vibe/projects.json)")
    if existing:
        print("  已在已有项目上启用；AGENTS.md 已存在未覆盖，协议入口需手动并入")
    print("下一步: 写 docs/CONTEXT.md 的 Domain:，然后 zcode ticket add / zcode ticket begin")


def cmd_install(args: list[str], quiet_root: Path | None = None) -> None:
    root = Path(args[0]) if args and Path(args[0]).is_dir() else quiet_root or find_repo_root()
    if root is None:
        raise TicketError("当前目录不是工单项目（缺少 tickets.md）")
    if not (root / ".git").exists():
        run_git(root, ["init", "--quiet"])
    hook_dir = root / ".vibe" / "hooks"
    hook_dir.mkdir(parents=True, exist_ok=True)
    hook_src = template_dir() / ".vibe" / "hooks" / "pre-commit"
    if hook_src.exists():
        shutil.copy2(hook_src, hook_dir / "pre-commit")
        (hook_dir / "pre-commit").chmod(0o755)
    else:
        raise TicketError("模板缺少 .vibe/hooks/pre-commit")
    run_git(root, ["config", "core.hooksPath", ".vibe/hooks"])
    cli = f"{sys.executable} -m zcode.cli"
    run_git(root, ["config", "zcode.cli", cli])
    print("✓ pre-commit hook 已安装 (core.hooksPath = .vibe/hooks)")


def _ask(prompt: str) -> str:
    """交互输入；非 TTY/EOF 时返回空（自动场景跳过提问）。"""
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def cmd_add(args: list[str]) -> None:
    root = find_repo_root()
    if root is None:
        raise TicketError("当前目录不是工单项目")
    tickets_file = root / "tickets.md"
    all_tickets = parse_tickets(tickets_file)

    title = args[0].strip() if args else ""
    if not title:
        title = _ask("工单标题（必填）: ")
        if not title:
            raise TicketError("标题不能为空")
    dep_input = _ask("依赖工单（可选，逗号分隔，回车跳过）: ") if len(args) < 2 else ""
    body = _ask("描述（可选，回车跳过）: ") if len(args) < 3 else ""

    deps = [d for d in re.split(r"[,;]", strip_inline_comment(dep_input)) if d.strip()]
    by_id = {t.id: t for t in all_tickets}
    bad_deps = [d for d in deps if d not in by_id]
    if bad_deps:
        raise TicketError(f"依赖不存在: {', '.join(bad_deps)}")

    max_num = 0
    for t in all_tickets:
        m = re.match(r"^T-(\d+)$", t.id)
        if m:
            max_num = max(max_num, int(m.group(1)))
    new_id = f"T-{max_num + 1:03d}"

    block = f"\n## {new_id} {title}\nStatus: backlog"
    if deps:
        block += "\nDepends: " + ", ".join(deps)
    if body:
        block += f"\n\n- [ ] {body}"
    block += "\n"
    with open(tickets_file, "a", encoding="utf-8") as f:
        f.write(block)
    add_log(root, "add", f"{new_id} ({title})")
    cmd_status(["-q"], root=root)
    print(f"✓ 已新增 {new_id}：{title}（Status: backlog）")
    print(f"拾取: zcode ticket begin {new_id}")


def cmd_begin(args: list[str]) -> None:
    if len(args) < 1:
        raise TicketError("用法: zcode ticket begin <ticket>")
    root = find_repo_root()
    if root is None:
        raise TicketError("当前目录不是工单项目")
    ctx_file = root / "docs/CONTEXT.md"
    tickets_file = root / "tickets.md"
    tid = args[0]
    by_id = {t.id: t for t in parse_tickets(tickets_file)}
    t = by_id.get(tid)
    if t is None:
        raise TicketError(f"工单 {tid} 不存在于 tickets.md")
    if t.status not in ("backlog", "blocked"):
        raise TicketError(f"工单 {tid} 当前状态是 {t.status}，只能从 backlog/blocked 开始")
    missing = [d for d in t.depends if not deps_done(by_id, [d])]
    if missing:
        names = ", ".join(
            f"{d}({by_id[d].status})" if d in by_id else f"{d}(不存在)" for d in missing
        )
        raise TicketError(f"依赖未满足: {names}。不能拾取 {tid}；若确实阻塞可先 zcode ticket transition {tid} blocked")

    mode = branch_mode(ctx_file)
    if mode == "auto":
        cur_branch = git_output(root, ["branch", "--show-current"])
        if cur_branch.startswith("vibe/") and cur_branch != f"vibe/{tid}":
            raise TicketError(f"当前已在工单分支 {cur_branch}，不能重复拾取；先 zcode ticket close 或手动切回主分支")
        if repo_has_commit(root):
            if not repo_clean(root):
                raise TicketError("工作区有未提交的源码改动，自动开分支前请先提交或 stash（BranchMode: manual 可关闭自动分支）")
            base = cur_branch or "HEAD"
            code, _ = run_git(root, ["switch", "-c", f"vibe/{tid}"])
            if code != 0:
                raise TicketError(f"创建分支 vibe/{tid} 失败")
            set_meta(root, "branch", f"vibe/{tid}")
            set_meta(root, "branch-base", base)
            add_log(root, "branch", f"created vibe/{tid} (from {base})")

    set_ticket_status(tickets_file, tid, "in-progress")
    set_anchor(ctx_file, "Phase", "analyze")
    set_anchor(ctx_file, "Current Ticket", tid)
    add_log(root, "begin", f"{tid} ({t.title})")
    cmd_status(["-q"], root=root)
    print(f"✓ 已拾取 {tid} ({t.title}) → in-progress，Phase=analyze")
    print("进入 analyze：更新 docs/CONTEXT.md 的 Domain:，新术语用 zcode ticket gloss add 记入术语表")


def cmd_phase(args: list[str]) -> None:
    if len(args) < 1:
        raise TicketError("用法: zcode ticket phase <name> [--green|--red|--pass|--reject|--force]")
    root = find_repo_root()
    if root is None:
        raise TicketError("当前目录不是工单项目")
    ctx_file = root / "docs/CONTEXT.md"
    to = args[0].lower()
    if to not in VALID_PHASES:
        raise TicketError(f"非法阶段 {to}，合法值: {' / '.join(VALID_PHASES)}")
    frm = get_anchor(ctx_file, "Phase")
    if not frm:
        raise TicketError("docs/CONTEXT.md 缺少 Phase: 锚点")
    frm = frm.lower()
    if not phase_legal(frm, to):
        raise TicketError(f"非法跃迁: {frm} → {to}（{frm} 只能到 {' / '.join(PHASE_TRANSITIONS[frm])} 或 analyze）")
    if not phase_guard(frm, to, root, args):
        raise TicketError("守卫未通过，阶段未切换")
    test_cmd = get_anchor(ctx_file, "TestCommand")
    if frm == "verify" and test_cmd:
        verify_evidence(root, frm, to, test_cmd)
    set_anchor(ctx_file, "Phase", to)
    flags = [a for a in args if a.startswith("--")]
    add_log(root, "phase", f"{frm} -> {to}{' ' + ' '.join(flags) if flags else ''}")
    cmd_status(["-q"], root=root)
    print(f"✓ Phase: {frm} → {to}")
    hints = {
        "analyze": "理解领域后，把工作拆成 tickets.md 工单",
        "plan": "确保 tickets.md 有本次工单及其任务项",
        "implement": "实现工单内容",
        "verify": "运行测试，绿后 zcode ticket phase review --green",
        "review": "对照标准+规范自查，通过后 zcode ticket phase commit --pass",
        "commit": "提交代码，然后 zcode ticket close 当前工单",
    }
    if to in hints:
        print(f"提示: {hints[to]}")


def cmd_transition(args: list[str]) -> None:
    if len(args) < 2:
        raise TicketError("用法: zcode ticket transition <ticket> <state>")
    root = find_repo_root()
    if root is None:
        raise TicketError("当前目录不是工单项目")
    tickets_file = root / "tickets.md"
    tid, to = args[0], args[1].lower()
    if to not in VALID_STATES:
        raise TicketError(f"非法状态 {to}，合法值: {' / '.join(VALID_STATES)}")
    t = get_ticket(tickets_file, tid)
    if t is None:
        raise TicketError(f"工单 {tid} 不存在于 tickets.md")
    frm = t.status or ""
    if not ticket_legal(frm, to):
        raise TicketError(f"非法跃迁: {frm} → {to}（{frm} 只能到 {' / '.join(TICKET_TRANSITIONS[frm])} 或无）")
    set_ticket_status(tickets_file, tid, to)
    add_log(root, "transition", f"{tid}: {frm} -> {to}")
    cmd_status(["-q"], root=root)
    print(f"✓ {tid}: {frm} → {to}")


# close 自动提交的范围：状态文件 + 自动生成的 CHANGELOG 条目（保持工作区干净，消灭收尾工单）
CLOSE_AUTO_COMMIT_PATHS = (
    "tickets.md", "docs/CONTEXT.md", "docs/UBIQUITOUS_LANGUAGE.md",
    "STATUS.md", "docs/ADR/", ".vibe/", "CHANGELOG.md",
)


def _bump_changelog_version(content: str) -> str:
    """从现有最高 [0.x.y] 推断下一版本号；解析失败退回 [0.1.0]。"""
    versions = [tuple(int(n) for n in m.groups()) for m in re.finditer(r"\[0\.(\d+)\.(\d+)\]", content)]
    if versions:
        major, minor = max(versions)
        return f"0.{major}.{minor + 1}"
    return "0.1.0"


def _auto_changelog(root: Path, t: Ticket) -> str | None:
    """CHANGELOG.md 缺工单号时自动补录，返回新条目文本；无文件/已有记录返回 None。"""
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return None
    content = read_text(changelog) or ""
    if t.id in content:
        return None
    date = datetime.now().strftime("%Y-%m-%d")
    version = _bump_changelog_version(content)
    entry = (
        f"## [{version}] - {date}\n\n"
        f"**{t.title}**（{t.id}）：{t.resolution or '（无修复记录）'}\n\n"
    )
    # 插入到第一个 `## [` 之前（保持最新条目在顶部）
    m = re.search(r"\n## \[", content)
    if m:
        content = content[: m.start() + 1] + entry + content[m.start() + 1:]
    else:
        content = content.rstrip("\n") + "\n\n" + entry
    write_text(changelog, content)
    return entry


def _auto_commit_state_files(root: Path, tid: str, title: str) -> bool:
    """自动提交状态文件 + CHANGELOG（绕过 hook：Phase=analyze 属协议内部收尾）。"""
    code, _ = run_git(root, ["add", "--", *CLOSE_AUTO_COMMIT_PATHS])
    if code != 0:
        return False
    _, out = run_git(root, ["status", "--porcelain", "--", *CLOSE_AUTO_COMMIT_PATHS])
    if not out:
        return False
    code, _ = run_git(root, ["-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", f"{tid} 状态收尾（{title}）"])
    return code == 0


def cmd_close(args: list[str]) -> None:
    if len(args) < 1:
        raise TicketError("用法: zcode ticket close <ticket>")
    root = find_repo_root()
    if root is None:
        raise TicketError("当前目录不是工单项目")
    ctx_file = root / "docs/CONTEXT.md"
    tickets_file = root / "tickets.md"
    tid = args[0]
    t = get_ticket(tickets_file, tid)
    if t is None:
        raise TicketError(f"工单 {tid} 不存在于 tickets.md")
    if t.status != "review":
        raise TicketError(f"工单 {tid} 状态是 {t.status}，只能 close review 状态（先 commit 再 close）")
    if not t.resolution:
        raise TicketError(f"工单 {tid} 缺少修复记录（Resolution: 为空）。先 zcode ticket resolve {tid} <根因+修复+验证> 再 close")
    if not ticket_committed(root, tid):
        raise TicketError(f"当前分支没有含 {tid} 的提交，拒绝 close（先 git commit，再 transition review + phase review）")
    # 文档同步：CHANGELOG.md 缺工单号时自动补录（不阻塞 close，杜绝"关了单文档没更新"）
    entry = _auto_changelog(root, t)
    if entry:
        print(f"✓ CHANGELOG 已自动记录 {tid}（{entry.strip().splitlines()[0]}）")

    mode = branch_mode(ctx_file)
    branch = get_meta(root, "branch")
    if mode == "auto" and branch:
        cur_branch = git_output(root, ["branch", "--show-current"])
        if cur_branch == branch:
            base = get_meta(root, "branch-base") or "main"
            if not repo_clean(root):
                raise TicketError(f"工作区有未提交的源码改动，先提交再 close（无法安全合并 {branch}）")
            code, _ = run_git(root, ["switch", base])
            if code != 0:
                raise TicketError(f"切回 {base} 失败")
            code, _ = run_git(root, ["merge", "--no-ff", branch])
            if code != 0:
                run_git(root, ["merge", "--abort"])
                raise TicketError(f"合并 {branch} → {base} 冲突/失败，已中止。请手动处理。")
            run_git(root, ["branch", "-d", branch])
            set_meta(root, "branch", "")
            set_meta(root, "branch-base", "")
            add_log(root, "branch", f"merged {branch} -> {base} and deleted")

    set_ticket_status(tickets_file, tid, "done")
    set_anchor(ctx_file, "Phase", "analyze")
    set_anchor(ctx_file, "Current Ticket", "")
    add_log(root, "close", f"{tid} ({t.title})")
    cmd_status(["-q"], root=root)
    print(f"✓ {tid} ({t.title}) → done，Phase 复位 analyze")
    # 自动提交状态文件，保持工作区干净（消灭"状态文件收尾"类工单）
    if _auto_commit_state_files(root, tid, t.title):
        print("✓ 状态文件已自动提交，工作区干净")


def cmd_status(args: list[str], root: Path | None = None) -> None:
    root = root or find_repo_root()
    if root is None:
        raise TicketError("当前目录不是工单项目")
    status_file = root / "STATUS.md"
    write_text(status_file, status_content(root))
    if "-q" not in args and "--quiet" not in args:
        print("✓ STATUS.md 已刷新")


def cmd_validate(args: list[str]) -> None:
    root = find_repo_root()
    if root is None:
        raise TicketError("当前目录不是工单项目")
    ctx_file = root / "docs/CONTEXT.md"
    tickets_file = root / "tickets.md"
    gloss_file = root / "docs/UBIQUITOUS_LANGUAGE.md"
    errors: list[str] = []

    if not ctx_file.exists():
        errors.append("缺少 docs/CONTEXT.md")
    else:
        phase = get_anchor(ctx_file, "Phase")
        if not phase:
            errors.append("CONTEXT.md 缺少 Phase: 锚点")
        elif phase.lower() not in VALID_PHASES:
            errors.append(f"Phase: {phase} 非法")

    tickets = parse_tickets(tickets_file)
    if not tickets:
        errors.append("tickets.md 没有工单")
    for t in tickets:
        if not t.status:
            errors.append(f"{t.id} 缺少 Status: 锚点")
        elif t.status not in VALID_STATES:
            errors.append(f"{t.id} Status: {t.status} 非法")
        for d in t.depends:
            if not get_ticket(tickets_file, d):
                errors.append(f"{t.id} 依赖的 {d} 不存在")
    if tickets and dep_cycle(tickets):
        errors.append("存在依赖环（工单互相依赖）")
    in_progress = [t.id for t in tickets if t.status == "in-progress"]
    if len(in_progress) > 1:
        errors.append(f"同时有多个 in-progress 工单: {', '.join(in_progress)}，只保留当前工单一个")
    for t in [t for t in tickets if t.status == "review" and not t.resolution]:
        errors.append(f"{t.id} 在 review 但缺少修复记录，close 前需 zcode ticket resolve {t.id} <根因+修复+验证>")

    cur = get_anchor(ctx_file, "Current Ticket")
    if cur:
        cur_t = get_ticket(tickets_file, cur)
        if not cur_t:
            errors.append(f"Current Ticket: {cur} 不存在")
        elif cur_t.status == "done":
            errors.append(f"Current Ticket: {cur} 已 done，应 begin 下个工单")

    status_file = root / "STATUS.md"
    if not status_file.exists():
        errors.append("缺少 STATUS.md，运行 zcode ticket status 生成")
    elif not status_fresh(root):
        errors.append("STATUS.md 已过期（状态有改动但未刷新），运行 zcode ticket status")

    if not gloss_file.exists():
        errors.append("缺少 docs/UBIQUITOUS_LANGUAGE.md 术语表")
    else:
        entries = parse_glossary(gloss_file)
        for e in [x for x in entries if not x["definition"]]:
            errors.append(f"术语表「{e['term']}」缺少 - **含义**：定义（zcode ticket gloss add 可补）")
        domain = get_anchor(ctx_file, "Domain")
        if domain and not entries:
            errors.append("Domain: 已填写但术语表为空，用 zcode ticket gloss add <术语> <定义> 记录")

    if errors:
        print(f"校验失败（{len(errors)} 个问题）:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("✓ validate 通过")


def _git_config(root: Path, key: str) -> str:
    code, out = run_git(root, ["config", "--get", key])
    return out[0].strip() if code == 0 and out else ""


def cmd_check_commit(args: list[str]) -> None:
    root = find_repo_root()
    if root is None or not (root / "docs/CONTEXT.md").exists():
        return  # 非工单项目，放行
    ctx_file = root / "docs/CONTEXT.md"
    tickets_file = root / "tickets.md"
    phase = get_anchor(ctx_file, "Phase")
    cur = get_anchor(ctx_file, "Current Ticket")
    problems: list[str] = []
    if phase not in ("verify", "review", "commit"):
        problems.append(f"Phase 是 '{phase}'，提交前需到 verify/review/commit（先 zcode ticket phase verify）")
    if cur:
        t = get_ticket(tickets_file, cur)
        if t and t.status == "in-progress":
            problems.append(f"当前工单 {cur} 还在 in-progress，需流转到 review/done 再提交")
    if not (root / "STATUS.md").exists():
        problems.append("STATUS.md 缺失，先运行 zcode ticket status 生成")
    elif not status_fresh(root):
        problems.append("STATUS.md 已过期（状态有改动但未刷新），先运行 zcode ticket status")
    domain = get_anchor(ctx_file, "Domain")
    if domain:
        gloss_file = root / "docs/UBIQUITOUS_LANGUAGE.md"
        if not gloss_file.exists():
            problems.append("缺少 docs/UBIQUITOUS_LANGUAGE.md 术语表（Domain 已填写）")
        elif not parse_glossary(gloss_file):
            problems.append("术语表为空（Domain 已填写），用 zcode ticket gloss add <术语> <定义> 记录")
    # 测试门禁：配了 TestCommand 则提交前真实执行，失败拦截；git config zcode.test-gate false 可关闭
    test_cmd = get_anchor(ctx_file, "TestCommand")
    if test_cmd and _git_config(root, "zcode.test-gate") != "false":
        r = subprocess.run(test_cmd, shell=True, capture_output=True, text=True, errors="replace")
        if r.returncode != 0:
            tail = (r.stderr or r.stdout or "").strip().splitlines()[-3:]
            problems.append(
                f"TestCommand 运行失败 (exit {r.returncode})，提交被拦截: {test_cmd}"
                + ("\n    " + "\n    ".join(tail) if tail else "")
            )
    if problems:
        print("commit 被 zcode 拦截:")
        for p in problems:
            print(f"  - {p}")
        if cur:
            print(f"处理: zcode ticket phase review --green; zcode ticket transition {cur} review; zcode ticket resolve {cur} <修复说明>; zcode ticket status; zcode ticket close {cur}")
        else:
            print("处理: 先 zcode ticket add/begin 一张工单推进到 review，或先 zcode ticket status 刷新后重试")
        print("（测试门禁可用 git config zcode.test-gate false 临时关闭）" if test_cmd else "")
        raise SystemExit(1)


def cmd_log(args: list[str]) -> None:
    root = find_repo_root()
    if root is None:
        raise TicketError("当前目录不是工单项目")
    log_file = root / ".vibe" / "log.md"
    if not log_file.exists():
        print("(还没有日志记录)")
        return
    lines = [l for l in read_lines(log_file) if l.strip()]
    for line in reversed(lines):
        print(line)


def cmd_context(args: list[str]) -> None:
    root = find_repo_root()
    if root is None:
        raise TicketError("当前目录不是工单项目")
    ctx_file = root / "docs/CONTEXT.md"
    tickets_file = root / "tickets.md"
    log_file = root / ".vibe" / "log.md"
    gloss_file = root / "docs/UBIQUITOUS_LANGUAGE.md"
    phase = get_anchor(ctx_file, "Phase")
    cur = get_anchor(ctx_file, "Current Ticket")
    domain = get_anchor(ctx_file, "Domain")
    if domain and len(domain) > 80:
        domain = domain[:80] + "…"
    tid = args[0] if args else cur
    if not tid:
        print("没有进行中的工单。zcode ticket next 看可拾取项；zcode ticket gloss 看术语表；zcode ticket log 看流转历史。")
        return
    t = get_ticket(tickets_file, tid)
    if t is None:
        raise TicketError(f"工单 {tid} 不存在于 tickets.md")
    by_id = {x.id: x for x in parse_tickets(tickets_file)}

    print("# zcode context — 按需摘要")
    print(f"Phase: {phase}")
    print(f"Current Ticket: {tid}")
    print(f"Domain: {domain}")
    print(f"术语表: {len(parse_glossary(gloss_file))} 条 (zcode ticket gloss 查看)")
    print()
    print(f"## {t.id} ({t.title}) [{t.status}]")
    print(t.block_text())
    if t.depends:
        print()
        print("## 依赖状态")
        for d in t.depends:
            dt = by_id.get(d)
            print(f"- {d} ({dt.title}) [{dt.status}]" if dt else f"- {d} (不存在)")
    if log_file.exists():
        lines = [l for l in read_lines(log_file) if l.strip()]
        if lines:
            print()
            print("## 最近流转")
            for line in lines[-5:]:
                print(line)


def cmd_gloss(args: list[str]) -> None:
    root = find_repo_root()
    if root is None:
        raise TicketError("当前目录不是工单项目")
    gloss_file = root / "docs/UBIQUITOUS_LANGUAGE.md"
    if not gloss_file.exists():
        raise TicketError(f"缺少 {gloss_file}")
    sub = args[0].lower() if args else ""
    entries = parse_glossary(gloss_file)

    if sub == "add":
        term = args[1].strip() if len(args) > 1 else ""
        if not term:
            term = _ask("术语名（必填）: ")
        if not term:
            raise TicketError("术语名不能为空")
        definition = " ".join(args[2:]) if len(args) > 2 else ""
        if not definition:
            definition = _ask("定义（一句话）: ")
        if not definition:
            raise TicketError("定义不能为空")
        if any(e["term"] == term for e in entries):
            raise TicketError(f"术语「{term}」已存在（zcode ticket gloss <term> 可查询）")
        write_text(gloss_file, (read_text(gloss_file) or "") + f"\n## {term}\n- **含义**：{definition}\n")
        add_log(root, "gloss", f"add {term}")
        cmd_status(["-q"], root=root)
        print(f"✓ 已记录术语「{term}」")
        return

    if sub:
        hits = [e for e in entries if e["term"].lower() == sub]
        if not hits:
            raise TicketError(f"术语「{sub}」不存在（zcode ticket gloss 看全部）")
        print(f"## {hits[0]['term']}")
        print(f"- **含义**：{hits[0]['definition']}")
        return

    if not entries:
        print("(术语表为空，用 zcode ticket gloss add <术语> <定义> 记录)")
        return
    for e in entries:
        print(f"## {e['term']}")
        print(f"- **含义**：{e['definition']}")


def cmd_resolve(args: list[str]) -> None:
    root = find_repo_root()
    if root is None:
        raise TicketError("当前目录不是工单项目")
    tickets_file = root / "tickets.md"
    if len(args) < 1:
        raise TicketError("用法: zcode ticket resolve <ticket> <根因+修复+验证>")
    tid = args[0]
    t = get_ticket(tickets_file, tid)
    if t is None:
        raise TicketError(f"工单 {tid} 不存在于 tickets.md")
    note = " ".join(args[1:]).strip() if len(args) > 1 else ""
    if not note:
        note = _ask("修复情况（根因+修复+验证）: ")
    if not note:
        raise TicketError("修复记录不能为空")
    set_ticket_anchor(tickets_file, tid, "Resolution", note)
    add_log(root, "resolve", f"{tid} ({t.title})")
    cmd_status(["-q"], root=root)
    print(f"✓ 已记录 {tid} 修复情况")


def cmd_next(args: list[str]) -> None:
    root = find_repo_root()
    if root is None:
        raise TicketError("当前目录不是工单项目")
    ctx_file = root / "docs/CONTEXT.md"
    tickets_file = root / "tickets.md"
    all_tickets = parse_tickets(tickets_file)
    by_id = {t.id: t for t in all_tickets}
    cur = get_anchor(ctx_file, "Current Ticket")

    open_tickets: list[Ticket] = []
    blocked_by_dep: list[tuple[Ticket, list[str]]] = []
    for t in all_tickets:
        if t.status != "backlog":
            continue
        missing = [d for d in t.depends if not (by_id.get(d) and by_id[d].status == "done")]
        if missing:
            blocked_by_dep.append((t, missing))
        else:
            open_tickets.append(t)
    open_tickets.sort(key=lambda t: t.id)
    blocked_by_dep.sort(key=lambda x: x[0].id)
    active = [t for t in all_tickets if t.status in ("in-progress", "review")]

    print("== 可拾取（依赖已就绪）==")
    if not open_tickets:
        print("  (无)")
    else:
        for t in open_tickets:
            print(f"  {t.id}  {t.title}")
    print("== 依赖未满足（backlog 但被阻塞）==")
    if not blocked_by_dep:
        print("  (无)")
    else:
        for t, missing in blocked_by_dep:
            m = ", ".join(
                f"{d}({by_id[d].status})" if d in by_id else f"{d}(不存在)" for d in missing
            )
            print(f"  {t.id}  {t.title}  <- 缺: {m}")
    print("== 进行中 / 审查中 ==")
    if not active:
        print("  (无)")
    else:
        for t in active:
            print(f"  {t.id}  {t.title}  [{t.status}]")
    if cur:
        print(f"当前工单: {cur}")


def cmd_projects(args: list[str]) -> None:
    reg = get_registry()
    if not reg:
        print("注册表为空。用 zcode ticket project-add <path> 登记，或 zcode ticket init 新项目。")
        return
    print("已登记项目：")
    for e in reg:
        ctx = Path(e.get("path", "")) / "docs/CONTEXT.md"
        phase = get_anchor(ctx, "Phase") or "-"
        cur = get_anchor(ctx, "Current Ticket") or "-"
        print(f"  {e.get('name')}  [{e.get('path')}]  Phase={phase}  Ticket={cur}")


def cmd_switch(args: list[str]) -> None:
    if len(args) < 1:
        raise TicketError("用法: zcode ticket switch <项目名|路径>")
    key = args[0]
    found = [e for e in get_registry() if e.get("name") == key or e.get("path") == key]
    if not found:
        raise TicketError(f"注册表里没有 {key}（用 zcode ticket project-add <path> 登记）")
    if len(found) > 1:
        raise TicketError("匹配到多个，请用完整路径指定")
    print(f"切到: {found[0]['path']}")
    print("提示: 直接 cd 到该目录即可（bash/zsh）；PowerShell 包装器可自动 cd")


def cmd_project_add(args: list[str]) -> None:
    if len(args) < 1:
        raise TicketError("用法: zcode ticket project-add <path>")
    p = str(Path.cwd()) if args[0] == "." else args[0]
    if not (Path(p) / "tickets.md").exists():
        raise TicketError(f"不是工单项目（缺少 tickets.md）: {p}")
    register_project(p)
    print(f"✓ 已登记: {p}")


def cmd_resolve_path(args: list[str]) -> None:
    if len(args) < 1:
        return
    key = args[0]
    found = [e for e in get_registry() if e.get("name") == key or e.get("path") == key]
    if len(found) == 1:
        print(found[0]["path"])


def cmd_ask(args: list[str]) -> None:
    topic = args[0].lower() if args else ""
    routes = [
        (r"^(init|new|开工|新建|初始化|project)$",
         ["→ 全新开工：zcode ticket init <name>（或 zcode ticket init . 当前目录）",
          "  铺工作台骨架 + git init + pre-commit hook + 项目登记。技能: workbench"]),
        (r"^(next|下一步|做什么|what)$",
         ["→ 看可拾取项：zcode ticket next",
          "  列出依赖已就绪可 begin 的工单；再配 zcode ticket status 看全局。"]),
        (r"^(status|状态|总览|overview)$",
         ["→ 全局状态：zcode ticket status（生成 STATUS.md），zcode ticket log 看历史，zcode ticket validate 做校验。"]),
        (r"^(log|历史|history)$",
         ["→ 流转历史：zcode ticket log（倒序查看 .vibe/log.md）"]),
        (r"^(validate|校验|check|检查)$",
         ["→ 一致性校验：zcode ticket validate（含依赖环检测、锚点合法性）"]),
        (r"^(begin|start|拾取|开工单)$",
         ["→ 拾取工单：zcode ticket begin T-XXX（依赖守卫 + BranchMode:auto 自动开分支）"]),
        (r"^(phase|阶段|progress|推进)$",
         ["→ 推进阶段：zcode ticket phase plan|implement|verify|review|commit",
          "  flags: --green 验证绿 | --red 验证红 | --pass 审查过 | --reject 打回 | --force 跳过产物守卫"]),
        (r"^(add|工单|ticket|新增)$",
         ["→ 新增工单：zcode ticket add \"标题\"（自动编号 T-XXX；不带标题则交互提问）"]),
        (r"^(transition|流转|blocked|状态改)$",
         ["→ 流转工单状态：zcode ticket transition <t> <s>",
          "  s ∈ backlog/in-progress/review/done/blocked（blocked 用于依赖未满足时记阻塞）"]),
        (r"^(close|关闭|done|完成)$",
         ["→ 关单：zcode ticket close T-XXX（需 review 状态 + 已有提交，自动合并分支）"]),
        (r"^(resolve|fix|修复|记录|resolution)$",
         ["→ 记录修复情况：zcode ticket resolve T-XXX <根因+修复+验证>",
          "  close 前必须，否则 close 会拒绝；validate 也会检查 review 工单的修复记录。"]),
        (r"^(context|上下文|接手|摘要|digest)$",
         ["→ 按需上下文：zcode ticket context（Phase / 当前工单全文 / 依赖 / 最近流转，读它代替全量读文件，省 token）"]),
        (r"^(gloss|glossary|术语|术语表)$",
         ["→ 术语表：zcode ticket gloss 列出；zcode ticket gloss <术语> 查；zcode ticket gloss add <术语> <定义> 记新词",
          "  Domain 已填但术语表为空会被 validate / pre-commit 拦截。"]),
        (r"^(projects|switch|切换|项目|multi)$",
         ["→ 多项目：zcode ticket projects 列全部；zcode ticket switch <name> 切目录；zcode ticket project-add <path> 登记"]),
        (r"^(install|hook|钩子)$",
         ["→ 安装 pre-commit hook：zcode ticket install（git config core.hooksPath = .vibe/hooks）"]),
        (r"^(commit|提交|拦截|blocked.*commit)$",
         ["→ 提交被拦：看报错。Phase 未到 verify/review/commit → 先 zcode ticket phase verify；工单 in-progress → 先 zcode ticket transition T-XXX review；STATUS.md 过期 → 先 zcode ticket status。"]),
    ]
    matched = False
    for pattern, lines in routes:
        if re.match(pattern, topic):
            for line in lines:
                print(line)
            matched = True
            break
    if not matched:
        print("给一个情境关键词：init / next / status / context / gloss / resolve / begin / phase / add / transition / close / projects / install / commit")
        print("（详细命令表见 zcode ticket help）")
    print()
    print("框架主动：Agent 接手工单仓库先读 STATUS.md 或跑 zcode ticket context；状态推进一律走命令，不手动改锚点。")


def show_help() -> None:
    print("工单工作台 — AI Vibe Coding 状态机工作流（Layer 2，vibe-workbench 移植）")
    print()
    print("用法: zcode ticket <command> [args]")
    print()
    print("  init <project|.>      铺工作台骨架（含 git init + hook + 项目登记；已有项目加 --existing）")
    print("  ask [topic]           情境路由：这个情况该用什么（如 zcode ticket ask commit）")
    print("  add [title]           交互式新增工单（自动编号，可带标题跳过提问）")
    print("  begin <ticket>        拾取工单 → in-progress, Phase=analyze（依赖守卫 + 自动开分支）")
    print("  phase <name> [flags]  推进阶段（守卫校验 + 验证证据留痕）")
    print("                         flags: --green 验证绿 | --red 验证红 | --pass 审查过 | --reject 打回 | --force 跳过产物守卫")
    print("  transition <t> <s>    流转工单（backlog→in-progress→review→done，blocked→backlog）")
    print("  close <ticket>        review→done（校验 Resolution + 已提交 + 自动合并分支），Phase 复位 analyze")
    print("  resolve <t> <note>    记录工单修复情况（根因+修复+验证）；close 前必须")
    print("  context [ticket]      按需上下文摘要（接手仓库先跑它，省 token）")
    print("  gloss [term|add]      术语表：列出 / 查询 / zcode ticket gloss add <术语> <定义>")
    print("  status                生成 STATUS.md 单屏总览（状态命令会自动刷新）")
    print("  validate              全量一致性校验（含依赖环、术语表、STATUS 保鲜）")
    print("  next                  建议下一步：可拾取/依赖未满足/进行中")
    print("  log                   倒序查看流转历史 (.vibe/log.md)")
    print("  install               安装 pre-commit hook 到当前仓库")
    print("  projects              列出已登记项目及各自状态")
    print("  switch <name>         切到项目目录（bash/zsh 打印路径）")
    print("  project-add <path>    登记项目到注册表 (~/.vibe/projects.json)")
    print("  check-commit          pre-commit hook 入口（提交前状态机校验）")
    print()
    print("阶段机: analyze → plan → implement → verify → review → commit → analyze")
    print("工单机: backlog → in-progress → review → done （in-progress/review 可 → blocked → backlog）")
    print("锚点:  docs/CONTEXT.md 的 Phase/Current Ticket/Domain/TestCommand/BranchMode")


def run(argv: list[str]) -> int:
    """分发 zcode ticket <cmd> <args...>。返回进程退出码。"""
    if not argv:
        show_help()
        return 0
    command = argv[0].lower()
    args = argv[1:]
    try:
        if command == "init":
            cmd_init(args)
        elif command == "ask":
            cmd_ask(args)
        elif command == "begin":
            cmd_begin(args)
        elif command == "phase":
            cmd_phase(args)
        elif command == "transition":
            cmd_transition(args)
        elif command == "close":
            cmd_close(args)
        elif command == "resolve":
            cmd_resolve(args)
        elif command == "context":
            cmd_context(args)
        elif command in ("gloss", "glossary"):
            cmd_gloss(args)
        elif command == "status":
            cmd_status(args)
        elif command == "validate":
            cmd_validate(args)
        elif command == "install":
            cmd_install(args)
        elif command == "check-commit":
            return cmd_check_commit(args)
        elif command == "add":
            cmd_add(args)
        elif command == "log":
            cmd_log(args)
        elif command == "next":
            cmd_next(args)
        elif command == "projects":
            cmd_projects(args)
        elif command == "switch":
            cmd_switch(args)
        elif command == "project-add":
            cmd_project_add(args)
        elif command == "resolve-path":
            cmd_resolve_path(args)
        elif command in ("help", "--help", "-h"):
            show_help()
        else:
            print(f"未知命令: {command}", file=sys.stderr)
            show_help()
            return 1
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    except TicketError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    return 0
