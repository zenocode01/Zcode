"""ticket.py（工单驱动工作台）单元与集成测试。

覆盖：锚点读写、工单/术语表解析、状态机跃迁、守卫、依赖环检测、
STATUS 生成器保鲜（CRLF / 生成器注释兼容）、init --existing、
完整命令流（add/begin/phase/transition/resolve/close）、check-commit 门禁。
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zcode import ticket  # noqa: E402


def _git(root: Path, *args: str) -> int:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True).returncode


class TicketBase(unittest.TestCase):
    """临时目录 + 项目脚手架。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.old_cwd = Path.cwd()
        self.old_registry = ticket.REGISTRY
        self.old_ask = ticket._ask
        ticket.REGISTRY = self.base / "projects.json"
        ticket._ask = lambda prompt: ""  # 自动化：跳过交互提问
        self.addCleanup(self._restore)

    def _restore(self):
        ticket.REGISTRY = self.old_registry
        ticket._ask = self.old_ask
        os.chdir(self.old_cwd)
        self._tmp.cleanup()

    def make_project(self, name: str = "proj") -> Path:
        """建一个已 init 的工单项目并 chdir 进去。"""
        proj = self.base / name
        ticket.cmd_init([str(proj)])
        os.chdir(proj)
        self._set_anchor(proj, "Domain", "测试领域")
        return proj

    def _set_anchor(self, root: Path, anchor: str, value: str) -> None:
        ctx = root / "docs/CONTEXT.md"
        ctx.write_text(ctx.read_text(encoding="utf-8") + f"\n{anchor}: {value}\n", encoding="utf-8")
        # set_anchor 只在锚点存在时替换；CONTEXT 模板缺 Domain 时直接追加
        ticket.set_anchor(ctx, anchor, value)

    def write_ctx(self, root: Path, content: str) -> None:
        (root / "docs/CONTEXT.md").write_text(content, encoding="utf-8")


# ---------- 锚点读写 ----------
class TestAnchors(TicketBase):
    def test_get_anchor_missing(self):
        f = self.base / "x.md"
        f.write_text("# hi\n", encoding="utf-8")
        self.assertIsNone(ticket.get_anchor(f, "Phase"))

    def test_get_anchor_with_inline_comment(self):
        f = self.base / "x.md"
        f.write_text("Status: in-progress          # backlog / in-progress\n", encoding="utf-8")
        self.assertEqual(ticket.get_anchor(f, "Status"), "in-progress          # backlog / in-progress")

    def test_set_anchor_replaces(self):
        f = self.base / "x.md"
        f.write_text("Phase: analyze\nother: 1\n", encoding="utf-8")
        self.assertTrue(ticket.set_anchor(f, "Phase", "verify"))
        self.assertEqual(ticket.get_anchor(f, "Phase"), "verify")

    def test_set_anchor_returns_false_when_absent(self):
        f = self.base / "x.md"
        f.write_text("other: 1\n", encoding="utf-8")
        self.assertFalse(ticket.set_anchor(f, "Phase", "verify"))


# ---------- 工单 / 术语表解析 ----------
class TestParse(TicketBase):
    def _tickets_file(self) -> Path:
        f = self.base / "tickets.md"
        f.write_text(
            "# 工单\n"
            "```markdown\n### T-000 示例\nStatus: done\n```\n"
            "\n## T-001 实现 A\nStatus: in-progress  # 注释\nDepends: T-002\n"
            "Resolution: 根因/修复/验证\n- [ ] 任务\n"
            "\n## T-002 实现 B\nStatus: backlog\nDepends: T-001, T-003; T-004\n"
            "\n## T-003 实现 C\nStatus: backlog\n",
            encoding="utf-8",
        )
        return f

    def test_parse_tickets_fence_and_anchors(self):
        ts = ticket.parse_tickets(self._tickets_file())
        ids = [t.id for t in ts]
        self.assertEqual(ids, ["T-001", "T-002", "T-003"])  # 围栏内示例不解析
        t1 = ts[0]
        self.assertEqual(t1.status, "in-progress")
        self.assertEqual(t1.depends, ["T-002"])
        self.assertEqual(t1.resolution, "根因/修复/验证")
        self.assertEqual(ts[1].depends, ["T-001", "T-003", "T-004"])

    def test_set_ticket_status(self):
        f = self._tickets_file()
        self.assertTrue(ticket.set_ticket_status(f, "T-002", "review"))
        t = ticket.get_ticket(f, "T-002")
        self.assertEqual(t.status, "review")
        self.assertEqual(ticket.get_ticket(f, "T-001").status, "in-progress")

    def test_set_ticket_anchor_insert_after_header(self):
        f = self._tickets_file()
        ticket.set_ticket_anchor(f, "T-003", "Resolution", "新记录")
        t = ticket.get_ticket(f, "T-003")
        self.assertEqual(t.resolution, "新记录")
        text = f.read_text(encoding="utf-8")
        self.assertLess(text.index("## T-003"), text.index("Resolution: 新记录"))

    def test_set_ticket_anchor_replace(self):
        f = self._tickets_file()
        ticket.set_ticket_anchor(f, "T-001", "Resolution", "覆盖")
        self.assertEqual(ticket.get_ticket(f, "T-001").resolution, "覆盖")

    def test_parse_glossary(self):
        f = self.base / "g.md"
        f.write_text(
            "```markdown\n## 假词条\n- **含义**：不解析\n```\n\n## 工单\n- **含义**：任务单元\n"
            "- **别名**：ticket\n\n## 缺定义词条\n- **其他**：x\n",
            encoding="utf-8",
        )
        entries = ticket.parse_glossary(f)
        self.assertEqual(entries[0]["term"], "工单")
        self.assertEqual(entries[0]["definition"], "任务单元")
        self.assertIsNone(entries[1]["definition"])


# ---------- 状态机 / 依赖 ----------
class TestStateMachine(TicketBase):
    def test_phase_legal_matrix(self):
        legal = {
            "analyze": ["plan", "analyze"],
            "plan": ["implement", "analyze"],
            "implement": ["verify", "analyze"],
            "verify": ["review", "implement", "analyze"],
            "review": ["commit", "implement", "analyze"],
            "commit": ["analyze"],
        }
        for frm in ticket.VALID_PHASES:
            for to in ticket.VALID_PHASES:
                expected = frm == to or to == "analyze" or to in ticket.PHASE_TRANSITIONS[frm]
                self.assertEqual(ticket.phase_legal(frm, to), expected, f"{frm}->{to}")

    def test_ticket_legal_matrix(self):
        for frm in ticket.VALID_STATES:
            for to in ticket.VALID_STATES:
                expected = to in ticket.TICKET_TRANSITIONS[frm]
                self.assertEqual(ticket.ticket_legal(frm, to), expected, f"{frm}->{to}")

    def _tickets(self):
        return [
            ticket.Ticket(id="T-001", title="a", status="done", depends=[]),
            ticket.Ticket(id="T-002", title="b", status="backlog", depends=["T-001"]),
            ticket.Ticket(id="T-003", title="c", status="backlog", depends=["T-002"]),
        ]

    def test_dep_cycle_none(self):
        self.assertFalse(ticket.dep_cycle(self._tickets()))

    def test_dep_cycle_detected(self):
        ts = self._tickets()
        ts.append(ticket.Ticket(id="T-004", title="d", status="backlog", depends=["T-003"]))
        ts[0].depends = ["T-004"]  # T-001 -> T-004 -> T-003 -> T-002 -> T-001
        self.assertTrue(ticket.dep_cycle(ts))

    def test_dep_cycle_unknown_dep_ignored(self):
        ts = self._tickets()
        ts[1].depends = ["T-999"]  # 不存在依赖不构成环
        self.assertFalse(ticket.dep_cycle(ts))


# ---------- STATUS 生成器与保鲜 ----------
class TestStatus(TicketBase):
    def test_status_content_fresh(self):
        root = self.make_project()
        ticket.cmd_status(["-q"], root=root)
        self.assertTrue(ticket.status_fresh(root))

    def test_status_stale_after_manual_change(self):
        root = self.make_project()
        ticket.cmd_status(["-q"], root=root)
        ctx = root / "docs/CONTEXT.md"
        ctx.write_text(ctx.read_text(encoding="utf-8").replace("Phase: analyze", "Phase: plan"), encoding="utf-8")
        self.assertFalse(ticket.status_fresh(root))

    def test_status_normalized_crlf_and_vibe_comment(self):
        root = self.make_project()
        content = ticket.status_content(root)
        # 模拟 vibe-workbench 生成的 CRLF + GENERATED-BY-VIBE 版本
        vibe_version = content.replace("\n", "\r\n").replace("GENERATED-BY-ZCODE", "GENERATED-BY-VIBE")
        self.assertEqual(
            ticket._status_normalized(vibe_version),
            ticket._status_normalized(content),
        )

    def test_status_contains_anchors_and_glossary_count(self):
        root = self.make_project()
        ticket.cmd_gloss(["add", "术语", "定义"])
        ticket.cmd_add(["一张工单"])
        ticket.cmd_status(["-q"], root=root)
        text = (root / "STATUS.md").read_text(encoding="utf-8")
        self.assertIn("Phase: analyze", text)
        self.assertIn("术语表: 1 条", text)
        self.assertIn("T-001", text)


# ---------- 完整命令流（集成） ----------
class TestLifecycle(TicketBase):
    def _full_project(self) -> Path:
        root = self.make_project()
        ticket.cmd_gloss(["add", "CLI", "命令行接口"])
        ticket.cmd_add(["实现 foo"])
        return root

    def test_add_begin_phase_guard(self):
        root = self._full_project()
        t = ticket.get_ticket(root / "tickets.md", "T-001")
        self.assertEqual(t.status, "backlog")
        ticket.cmd_begin(["T-001"])
        self.assertEqual(ticket.get_ticket(root / "tickets.md", "T-001").status, "in-progress")
        self.assertEqual(ticket.get_anchor(root / "docs/CONTEXT.md", "Phase"), "analyze")
        self.assertEqual(ticket.get_anchor(root / "docs/CONTEXT.md", "Current Ticket"), "T-001")

    def test_phase_guard_blocks_analyze_to_plan_without_domain(self):
        root = self.make_project()
        ticket.cmd_add(["x"])
        ctx = root / "docs/CONTEXT.md"
        ctx.write_text(ctx.read_text(encoding="utf-8").replace("Domain: 测试领域\n", "Domain:\n"), encoding="utf-8")
        ticket.cmd_begin(["T-001"])
        with self.assertRaises(ticket.TicketError):
            ticket.cmd_phase(["plan"])
        self.assertEqual(ticket.get_anchor(ctx, "Phase"), "analyze")

    def test_verify_gate_requires_green_flag(self):
        root = self._full_project()
        (root / "test_x.py").write_text("", encoding="utf-8")  # 满足 implement→verify 产物守卫
        ticket.cmd_begin(["T-001"])
        ticket.cmd_phase(["plan"])
        ticket.cmd_phase(["implement"])
        ticket.cmd_phase(["verify"])
        with self.assertRaises(ticket.TicketError):
            ticket.cmd_phase(["review"])  # 无 --green
        self.assertEqual(ticket.get_anchor(root / "docs/CONTEXT.md", "Phase"), "verify")
        ticket.cmd_phase(["review", "--green"])
        self.assertEqual(ticket.get_anchor(root / "docs/CONTEXT.md", "Phase"), "review")

    def test_illegal_transition_rejected(self):
        root = self._full_project()
        ticket.cmd_begin(["T-001"])
        with self.assertRaises(ticket.TicketError):
            ticket.cmd_transition(["T-001", "done"])
        self.assertEqual(ticket.get_ticket(root / "tickets.md", "T-001").status, "in-progress")

    def test_dependency_guard(self):
        root = self.make_project()
        ticket.cmd_add(["依赖 A"])
        ticket.cmd_add(["依赖 B"])
        # T-002 依赖 T-001：手动补 Depends 锚点再验证
        tickets = root / "tickets.md"
        text = tickets.read_text(encoding="utf-8")
        tickets.write_text(text.replace("## T-002 依赖 B\nStatus: backlog", "## T-002 依赖 B\nStatus: backlog\nDepends: T-001"), encoding="utf-8")
        with self.assertRaises(ticket.TicketError):
            ticket.cmd_begin(["T-002"])  # T-001 未 done

    def _drive_to_commit_phase(self, root: Path) -> None:
        """（已 begin）一路推到 commit 阶段（含测试产物）。"""
        (root / "test_x.py").write_text("", encoding="utf-8")
        ticket.cmd_phase(["plan"])
        ticket.cmd_phase(["implement"])
        ticket.cmd_phase(["verify", "--green"])
        ticket.cmd_transition(["T-001", "review"])
        ticket.cmd_resolve(["T-001", "根因; 修复; 验证"])
        ticket.cmd_phase(["review", "--green"])
        ticket.cmd_phase(["commit", "--pass"])

    def _commit_no_hook(self, root: Path, msg: str) -> int:
        """绕过 pre-commit hook 提交（hook 行为由 TestCheckCommit 单独覆盖）。"""
        return subprocess.run(
            ["git", "-C", str(root), "-c", "core.hooksPath=/dev/null", "add", "-A"],
            capture_output=True, text=True,
        ).returncode + subprocess.run(
            ["git", "-C", str(root), "-c", "core.hooksPath=/dev/null", "commit", "-m", msg],
            capture_output=True, text=True,
        ).returncode

    def test_full_close_without_initial_commit(self):
        root = self._full_project()
        ticket.cmd_begin(["T-001"])
        self._drive_to_commit_phase(root)
        self.assertEqual(self._commit_no_hook(root, "T-001 实现 foo"), 0)
        ticket.cmd_close(["T-001"])
        self.assertEqual(ticket.get_ticket(root / "tickets.md", "T-001").status, "done")
        self.assertEqual(ticket.get_anchor(root / "docs/CONTEXT.md", "Phase"), "analyze")

    def test_close_requires_resolution_and_commit(self):
        root = self._full_project()
        (root / "test_x.py").write_text("", encoding="utf-8")
        ticket.cmd_begin(["T-001"])
        ticket.cmd_phase(["plan"])
        ticket.cmd_phase(["implement"])
        ticket.cmd_phase(["verify", "--green"])
        ticket.cmd_transition(["T-001", "review"])
        with self.assertRaises(ticket.TicketError):
            ticket.cmd_close(["T-001"])  # 无 Resolution
        ticket.cmd_resolve(["T-001", "根因; 修复; 验证"])
        with self.assertRaises(ticket.TicketError):
            ticket.cmd_close(["T-001"])  # 未提交
        self.assertEqual(ticket.get_ticket(root / "tickets.md", "T-001").status, "review")

    def test_repo_clean_ignores_docs_and_state_files(self):
        root = self.make_project()
        _git(root, "config", "user.email", "t@t")
        _git(root, "config", "user.name", "t")
        self.assertEqual(self._commit_no_hook(root, "seed"), 0)
        (root / "README.md").write_text("改文档", encoding="utf-8")
        (root / "CHANGELOG.md").write_text("改日志", encoding="utf-8")
        (root / "tickets.md").write_text("改工单", encoding="utf-8")
        self.assertTrue(ticket.repo_clean(root))  # 文档+状态文件不算脏
        (root / "src_code.py").write_text("print(1)", encoding="utf-8")
        self.assertFalse(ticket.repo_clean(root))  # 源码改动算脏

    def test_close_auto_appends_changelog_and_commits(self):
        """缺 CHANGELOG 记录 → 自动补录（含 T-XXX）+ 状态文件自动提交，close 通过。"""
        root = self._full_project()
        (root / "CHANGELOG.md").write_text("# Changelog\n\n## [0.5.0]\n- 其他变更\n", encoding="utf-8")
        ticket.cmd_begin(["T-001"])
        self._drive_to_commit_phase(root)
        self.assertEqual(self._commit_no_hook(root, "T-001 实现 foo"), 0)
        ticket.cmd_close(["T-001"])  # 不再拒绝：自动补录
        self.assertEqual(ticket.get_ticket(root / "tickets.md", "T-001").status, "done")
        changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("T-001", changelog)
        self.assertIn("## [0.5.1]", changelog)  # 版本自动 bump
        # 状态文件已自动提交：工作区无状态文件残留
        _, out = ticket.run_git(root, ["status", "--porcelain"])
        self.assertFalse(any("tickets.md" in l or "STATUS.md" in l for l in out))
        # 自动提交的 message 含工单号
        code, out = ticket.run_git(root, ["log", "--oneline", "--grep=T-001", "-1"])
        self.assertEqual(code, 0)

    def test_close_changelog_no_duplicate(self):
        """CHANGELOG 已有记录 → 不重复追加。"""
        root = self._full_project()
        (root / "CHANGELOG.md").write_text("# Changelog\n\n## [0.1.0]\n- T-001 已记录\n", encoding="utf-8")
        ticket.cmd_begin(["T-001"])
        self._drive_to_commit_phase(root)
        self.assertEqual(self._commit_no_hook(root, "T-001 实现 foo"), 0)
        ticket.cmd_close(["T-001"])
        text = (root / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("T-001"), 1)  # 只保留原有那条

    def test_close_no_changelog_file_no_create(self):
        root = self._full_project()  # 无 CHANGELOG.md
        ticket.cmd_begin(["T-001"])
        self._drive_to_commit_phase(root)
        self.assertEqual(self._commit_no_hook(root, "T-001 实现 foo"), 0)
        ticket.cmd_close(["T-001"])
        self.assertFalse((root / "CHANGELOG.md").exists())  # 不创建
        self.assertEqual(ticket.get_ticket(root / "tickets.md", "T-001").status, "done")

    def test_close_allows_no_changelog_file(self):
        root = self._full_project()  # 无 CHANGELOG.md → 守卫跳过
        ticket.cmd_begin(["T-001"])
        self._drive_to_commit_phase(root)
        self.assertEqual(self._commit_no_hook(root, "T-001 实现 foo"), 0)
        ticket.cmd_close(["T-001"])
        self.assertEqual(ticket.get_ticket(root / "tickets.md", "T-001").status, "done")

    def test_auto_branch_create_and_merge(self):
        root = self.make_project()
        _git(root, "config", "user.email", "t@t")
        _git(root, "config", "user.name", "t")
        (root / "seed.txt").write_text("x", encoding="utf-8")
        self.assertEqual(self._commit_no_hook(root, "seed"), 0)
        _, base_out = ticket.run_git(root, ["branch", "--show-current"])
        base_branch = base_out[0].strip()  # master 或 main（取决于 git 配置）
        ticket.cmd_add(["带分支工单"])
        ticket.cmd_begin(["T-001"])
        code, out = ticket.run_git(root, ["branch", "--show-current"])
        self.assertEqual(out[0].strip(), "vibe/T-001")
        self._drive_to_commit_phase(root)
        self.assertEqual(self._commit_no_hook(root, "T-001 带分支工单"), 0)
        ticket.cmd_close(["T-001"])
        code, out = ticket.run_git(root, ["branch", "--show-current"])
        self.assertEqual(out[0].strip(), base_branch)  # 回到原基线分支
        code, _ = ticket.run_git(root, ["rev-parse", "--verify", "refs/heads/vibe/T-001"])
        self.assertNotEqual(code, 0)  # 分支已删除
        self.assertTrue(ticket.ticket_committed(root, "T-001"))


# ---------- init --existing ----------
class TestInitExisting(TicketBase):
    def test_existing_project_no_overwrite(self):
        proj = self.base / "existing"
        proj.mkdir()
        (proj / "AGENTS.md").write_text("原内容", encoding="utf-8")
        (proj / "src").mkdir()
        (proj / "src" / "main.py").write_text("print(1)", encoding="utf-8")
        ticket.cmd_init([str(proj), "--existing"])
        agents = (proj / "AGENTS.md").read_text(encoding="utf-8")
        self.assertTrue(agents.startswith("原内容"))  # 原内容保留在开头
        self.assertIn("工单工作台协议", agents)  # 协议段自动追加
        self.assertEqual((proj / "src" / "main.py").read_text(encoding="utf-8"), "print(1)")
        self.assertTrue((proj / "tickets.md").exists())
        self.assertTrue((proj / "docs/CONTEXT.md").exists())
        self.assertTrue((proj / ".vibe" / "hooks" / "pre-commit").exists())
        if os.name != "nt":  # Windows 无 POSIX 权限位
            self.assertTrue((proj / ".vibe" / "hooks" / "pre-commit").stat().st_mode & 0o111)

    def test_init_refuses_nonempty_without_flag(self):
        proj = self.base / "n" 
        proj.mkdir()
        (proj / "x").write_text("1", encoding="utf-8")
        with self.assertRaises(ticket.TicketError):
            ticket.cmd_init([str(proj)])

    def test_existing_auto_appends_agents_protocol(self):
        proj = self.base / "p"
        proj.mkdir()
        (proj / "AGENTS.md").write_text("# 我的项目\n\n原内容\n", encoding="utf-8")
        ticket.cmd_init([str(proj), "--existing"])
        text = (proj / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("# 我的项目", text)
        self.assertIn("原内容", text)  # 原内容保留
        self.assertIn("工单工作台协议", text)  # 自动追加
        # 幂等：再跑一次不重复追加
        ticket.cmd_init([str(proj), "--existing"])
        self.assertEqual((proj / "AGENTS.md").read_text(encoding="utf-8").count("工单工作台协议"), 1)

    def test_init_guided_setup_writes_domain_and_testcommand(self):
        proj = self.base / "g"
        ticket.cmd_init([str(proj)])
        ticket._ask = lambda prompt: "记账项目" if "Domain" in prompt else "pytest"
        ticket._init_guided_setup(proj)
        ctx = proj / "docs/CONTEXT.md"
        self.assertEqual(ticket.get_anchor(ctx, "Domain"), "记账项目")
        self.assertEqual(ticket.get_anchor(ctx, "TestCommand"), "pytest")


# ---------- check-commit 门禁 ----------
class TestCheckCommit(TicketBase):
    def _project_at_commit_phase(self, test_cmd: str) -> Path:
        root = self.make_project()
        self._set_anchor(root, "TestCommand", "exit 0")  # 先保证 verify 阶段能绿
        ticket.cmd_gloss(["add", "CLI", "命令行接口"])
        ticket.cmd_add(["x"])
        (root / "test_x.py").write_text("", encoding="utf-8")
        ticket.cmd_begin(["T-001"])
        ticket.cmd_phase(["plan"])
        ticket.cmd_phase(["implement"])
        ticket.cmd_phase(["verify", "--green"])
        ticket.cmd_transition(["T-001", "review"])
        ticket.cmd_resolve(["T-001", "根因; 修复; 验证"])
        ticket.cmd_phase(["review", "--green"])
        ticket.cmd_phase(["commit", "--pass"])
        # 之后再换成目标 TestCommand（门禁场景专用）
        if test_cmd:
            self._set_anchor(root, "TestCommand", test_cmd)
            ticket.cmd_status(["-q"], root=root)  # 刷新 STATUS 避免过期误拦
        return root

    def test_check_commit_blocks_bad_phase(self):
        root = self.make_project()
        ticket.cmd_add(["x"])
        ticket.cmd_begin(["T-001"])  # Phase=analyze
        with self.assertRaises(SystemExit):
            ticket.cmd_check_commit([])

    def test_test_gate_blocks_failing_test(self):
        root = self._project_at_commit_phase("exit 1")
        with self.assertRaises(SystemExit):
            ticket.cmd_check_commit([])

    def test_test_gate_passes_green_test(self):
        root = self._project_at_commit_phase("exit 0")
        ticket.cmd_check_commit([])  # 不应抛异常

    def test_test_gate_can_be_disabled(self):
        root = self._project_at_commit_phase("exit 1")
        _git(root, "config", "zcode.test-gate", "false")
        ticket.cmd_check_commit([])  # 关闭后放行

    def test_test_gate_skipped_without_testcommand(self):
        root = self._project_at_commit_phase("exit 0")
        ctx = root / "docs/CONTEXT.md"
        ctx.write_text(ctx.read_text(encoding="utf-8").replace("TestCommand: exit 0\n", "TestCommand:\n"), encoding="utf-8")
        ticket.cmd_status(["-q"], root=root)
        ticket.cmd_check_commit([])


if __name__ == "__main__":
    unittest.main()
