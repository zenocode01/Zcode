"""workflow.py / handoff.py / marketplace.py / profile.py 单元测试。"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zcode import handoff, marketplace, profile, workflow  # noqa: E402


class TestWorkflow(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _wf(self, text: str) -> Path:
        f = self.base / "wf.yaml"
        f.write_text(text, encoding="utf-8")
        return f

    def test_load_and_list(self):
        self._wf("name: demo\ndescription: 演示\nsteps:\n  - prompt: hello\n")
        wf = workflow.load_workflow(self.base / "wf.yaml")
        self.assertEqual(wf.name, "demo")
        self.assertEqual(wf.steps[0].kind, "prompt")

    def test_load_missing_fields(self):
        self._wf("name: demo\n")
        with self.assertRaises(ValueError):
            workflow.load_workflow(self.base / "wf.yaml")

    def test_load_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            workflow.load_workflow(self.base / "nope.yaml")

    def test_step_from_dict_rejects_unknown(self):
        with self.assertRaises(ValueError):
            workflow.Step.from_dict({"bogus": 1})

    def test_plan_conditions(self):
        self._wf(
            "name: c\ndescription: d\nsteps:\n"
            "  - prompt: a\n    when: '${flag}'\n"
            "  - prompt: b\n    when: 'false'\n"
            "  - prompt: c\n",
        )
        wf = workflow.load_workflow(self.base / "wf.yaml")
        plan = workflow.plan_workflow(wf, {"flag": True})
        self.assertEqual([p["index"] for p in plan if p.get("skipped")], [2])
        self.assertEqual(plan[0]["kind"], "prompt")
        plan2 = workflow.plan_workflow(wf, {"flag": False})
        self.assertEqual([p["index"] for p in plan2 if p.get("skipped")], [1, 2])

    def test_plan_skill_loads_instruction(self):
        self._wf("name: s\ndescription: d\nsteps:\n  - skill: tdd\n")
        wf = workflow.load_workflow(self.base / "wf.yaml")
        plan = workflow.plan_workflow(wf)
        self.assertEqual(plan[0]["skill"], "tdd")
        self.assertIn("tdd", plan[0]["instruction"].lower())

    def test_run_dry_run_does_not_execute(self):
        self._wf("name: r\ndescription: d\nsteps:\n  - command: echo SHOULD_NOT_RUN\n")
        wf = workflow.load_workflow(self.base / "wf.yaml")
        rc = workflow.run_workflow(wf, dry_run=True)
        self.assertEqual(rc, 0)

    def test_run_command_failure_returns_rc(self):
        self._wf("name: f\ndescription: d\nsteps:\n  - command: exit 3\n")
        wf = workflow.load_workflow(self.base / "wf.yaml")
        rc = workflow.run_workflow(wf, dry_run=False)
        self.assertEqual(rc, 3)


class TestHandoff(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _workbench_project(self) -> Path:
        """造一个 workbench 项目（有 tickets.md + CONTEXT 锚点）。"""
        proj = self.base / "wb"
        proj.mkdir()
        (proj / "tickets.md").write_text("## T-003 干活\nStatus: in-progress\n", encoding="utf-8")
        (proj / "docs").mkdir()
        (proj / "docs" / "CONTEXT.md").write_text(
            "Phase: implement\nCurrent Ticket: T-003\n", encoding="utf-8"
        )
        return proj

    def test_save_load_project_level(self):
        proj = self.base / "p"
        proj.mkdir()
        path = handoff.save_handoff(
            project_dir=proj, goal="目标", achieved=["a"], decisions=["d1"], next_steps=["n1"],
        )
        self.assertTrue(path.exists())
        self.assertTrue((proj / ".memory" / "handoff.md").exists())
        content = handoff.load_handoff(project_dir=proj)
        self.assertIn("目标", content)
        self.assertIn("a", content)
        self.assertIn("d1", content)

    def test_auto_ticket_status_in_workbench_project(self):
        proj = self._workbench_project()
        content = handoff.load_handoff(project_dir=proj)
        self.assertEqual(content, "")  # 尚未保存
        handoff.save_handoff(project_dir=proj, goal="G")
        content = handoff.load_handoff(project_dir=proj)
        self.assertIn("工单 T-003", content)  # 自动引用工单状态
        self.assertIn("阶段: implement", content)
        self.assertIn("STATUS.md", content)  # 指向单一事实来源

    def test_explicit_in_progress_overrides_auto(self):
        proj = self._workbench_project()
        handoff.save_handoff(project_dir=proj, goal="G", in_progress=["自定义事项"])
        content = handoff.load_handoff(project_dir=proj)
        self.assertIn("自定义事项", content)
        self.assertNotIn("工单 T-003", content)

    def test_auto_status_skipped_in_plain_project(self):
        proj = self.base / "plain"
        proj.mkdir()
        handoff.save_handoff(project_dir=proj, goal="G")
        content = handoff.load_handoff(project_dir=proj)
        self.assertIn("（空）", content)  # 无工作台 → 进行中为空节
        self.assertNotIn("工单 T-", content)

    def test_global_store(self):
        path = handoff.save_handoff(global_store=True, goal="全局")
        self.assertEqual(path, handoff.GLOBAL_HANDOFF)
        self.assertIn("全局", handoff.load_handoff(global_store=True))
        path.unlink(missing_ok=True)

    def test_load_missing_returns_empty(self):
        self.assertEqual(handoff.load_handoff(project_dir=self.base / "nope"), "")

    def test_save_empty_sections(self):
        proj = self.base / "p2"
        proj.mkdir()
        path = handoff.save_handoff(project_dir=proj, goal="")
        content = path.read_text(encoding="utf-8")
        self.assertIn("（空）", content)


class TestMarketplace(unittest.TestCase):
    def test_build_marketplace_counts_and_valid(self):
        market = marketplace.build_marketplace()
        self.assertEqual(market["count"], len(market["skills"]))
        self.assertGreaterEqual(market["count"], 10)
        valid = [s for s in market["skills"] if s["valid"]]
        self.assertEqual(len(valid), market["count"])  # 全部通过质量校验
        names = [s["name"] for s in market["skills"]]
        self.assertIn("tdd", names)
        self.assertIn("workbench", names)

    def test_validate_skill_unknown(self):
        issues = marketplace.validate_skill("no-such-skill")
        self.assertTrue(issues)


class TestProfile(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_load_profile_missing(self):
        with self.assertRaises(FileNotFoundError):
            profile.load_profile(self.base / "nope.yaml")

    def test_load_profile_minimal(self):
        f = self.base / "p.yaml"
        f.write_text("name: t\nmodel_family: qwen\ncontext_window: 8192\ntool_level: 1\n", encoding="utf-8")
        p = profile.load_profile(f)
        self.assertEqual(p.name, "t")
        self.assertEqual(p.model_family, "qwen")
        self.assertEqual(p.context_window, 8192)

    def test_load_real_profile(self):
        real = Path(__file__).resolve().parents[1] / "profiles" / "local-qwen3.6-35b.yaml"
        if real.exists():
            p = profile.load_profile(real)
            self.assertEqual(p.skill_variant, "local")


class TestPackageEntry(unittest.TestCase):
    """回归: `python -m zcode` 必须可用（bin/zcode.js npm 入口依赖它）。"""

    def test_python_dash_m_zcode_runs(self):
        r = subprocess.run(
            [sys.executable, "-m", "zcode", "skills", "list"],
            capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]),
        )
        self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")
        self.assertIn("tdd", r.stdout)


class TestInstallScript(unittest.TestCase):
    """回归: install.sh --project X --uninstall 必须只卸载项目目录（曾忽略
    --project 误删全局 ~/.agents/skills）。"""

    REPO = Path(__file__).resolve().parents[2]
    SCRIPT = REPO / "scripts" / "install.sh"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _run(self, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
        full_env = dict(os.environ)
        full_env.pop("ZCODE_HOME", None)
        if env:
            full_env.update(env)
        return subprocess.run(
            ["bash", str(self.SCRIPT), *args],
            capture_output=True, text=True, cwd=str(self.REPO), env=full_env,
        )

    def _proj_skills(self, name: str = "proj") -> Path:
        return self.base / name / ".agents" / "skills"

    def test_project_install_then_uninstall(self):
        if not self.SCRIPT.exists():
            self.skipTest("scripts/install.sh 不存在")
        proj = self._proj_skills()
        r = self._run("--project", str(self.base / "proj"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(proj.is_dir(), "项目级安装应创建 .agents/skills")
        self.assertTrue((proj / "tdd").is_symlink() or (proj / "tdd").exists())
        r = self._run("--project", str(self.base / "proj"), "--uninstall")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((proj / "tdd").exists(), "项目软链应被移除")
        self.assertIn("[项目级] 卸载", r.stdout, "应声明项目级卸载")
        global_tdd = Path.home() / ".agents/skills" / "tdd"
        if global_tdd.is_symlink():
            self.assertTrue(global_tdd.exists(), "uninstall 不得触碰全局 ~/.agents/skills")


if __name__ == "__main__":
    unittest.main()


# ---------- memory.py（MemStore 降级） ----------
class TestMemStore(unittest.TestCase):
    """MemStore.add 降级：infer 提取 0 条 → 自动 L0 原文写入（记忆不丢）+ degraded 标记。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        p = profile.Profile.from_dict({
            "name": "test", "model_family": "qwen-test",
            "context_window": 8192, "tool_level": 2,
            "memory": {
                "llm": {"base_url": "http://127.0.0.1:9/v1"},
                "embedder": {"provider": "zcode_http", "model": "m", "base_url": "http://127.0.0.1:9"},
                "vector_store": {"provider": "qdrant", "path": str(Path(self._tmp.name) / "mem")},
                "infer_mode": "simplified",
            },
        })
        from zcode.memory import MemStore
        self.ms = MemStore(p)

    def test_infer_empty_auto_degrade_to_l0(self):
        """infer 提取返回 0 条 → 自动降级第二次调用（infer=False 原文写入），degraded 标记。"""
        from unittest import mock
        with mock.patch.object(
            self.ms._mem, "add",
            side_effect=[{"results": []}, {"results": [{"id": "x1", "memory": "原文"}]}],
        ) as m:
            r = self.ms.add("需要记忆的原文", user_id="u", metadata={"k": "v"})
        self.assertEqual(r["results"][0]["id"], "x1")
        self.assertTrue(r.get("degraded"))
        self.assertEqual(len(m.call_args_list), 2)
        first, second = m.call_args_list
        self.assertTrue(first.kwargs["infer"])          # 第一次走 LLM 提取
        self.assertFalse(second.kwargs["infer"])        # 降级后纯 embedding
        self.assertEqual(second.kwargs["user_id"], "u")  # 参数透传
        self.assertEqual(second.kwargs["metadata"], {"k": "v"})

    def test_infer_success_no_degrade(self):
        """infer 提取有结果 → 单次调用，不降级。"""
        from unittest import mock
        with mock.patch.object(
            self.ms._mem, "add",
            return_value={"results": [{"id": "x1", "memory": "提取的事实"}]},
        ) as m:
            r = self.ms.add("内容")
        self.assertFalse(r.get("degraded"))
        m.assert_called_once()

    def test_l0_mode_no_retry(self):
        """infer_mode=none（L0）→ 单次 infer=False 调用，0 条不重试、不降级标记。"""
        from unittest import mock
        self.ms.infer_mode = "none"
        with mock.patch.object(self.ms._mem, "add", return_value={"results": []}) as m:
            r = self.ms.add("内容")
        m.assert_called_once()
        self.assertFalse(m.call_args.kwargs["infer"])
        self.assertFalse(r.get("degraded"))

    def test_cli_warns_on_degrade(self):
        """CLI 在降级时向 stderr 打印提示（不再静默 0 条）。"""
        import io
        import contextlib
        from unittest import mock
        from zcode import cli
        fake = mock.MagicMock()
        fake.infer_mode = "simplified"
        fake.add.return_value = {"results": [{"id": "x1", "memory": "原文"}], "degraded": True}
        with mock.patch.object(cli, "_load_memstore", return_value=fake):
            ns = mock.MagicMock(content="内容", user="u")
            buf = io.StringIO()
            with contextlib.redirect_stderr(buf):
                rc = cli.cmd_memory_add(ns)
        self.assertEqual(rc, 0)
        self.assertIn("降级", buf.getvalue())


# ---------- version 子命令 / 版本源 ----------
class TestVersion(unittest.TestCase):
    def test_init_version_matches_pyproject(self):
        """__version__ 与 pyproject.toml 一致（版本统一第五处，防再次漂移）。"""
        import tomllib
        import zcode
        py = Path(__file__).resolve().parents[1] / "pyproject.toml"
        with open(py, "rb") as f:
            pyver = tomllib.load(f)["project"]["version"]
        self.assertEqual(zcode.__version__, pyver)

    def test_version_command_prints(self):
        """zcode version 输出 zcode <版本>。"""
        import contextlib
        import io
        from unittest import mock
        from zcode import cli
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cli.main(["version"])
        self.assertEqual(rc, 0)
        self.assertRegex(buf.getvalue(), r"^zcode \d+\.\d+\.\d+")


# ---------- update 自更新命令 ----------
class TestUpdate(unittest.TestCase):
    """update.py：dry-run / 前置检查 / 分步执行与失败中止。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        _git = lambda *a: subprocess.run(
            ["git", "-C", str(self.root), *a], capture_output=True, text=True).returncode
        _git("init", "-q", ".")
        _git("config", "user.email", "t@t")
        _git("config", "user.name", "t")
        (self.root / "a.txt").write_text("x", encoding="utf-8")
        (self.root / "package.json").write_text("{}", encoding="utf-8")
        (self.root / "scripts").mkdir()
        (self.root / "scripts" / "install.sh").write_text("#!/bin/sh\n", encoding="utf-8")
        _git("add", "-A")
        _git("commit", "-q", "-m", "seed")

    def test_precheck_rejects_dirty(self):
        from zcode import update
        (self.root / "dirty.txt").write_text("x", encoding="utf-8")
        reason = update.precheck(self.root)
        self.assertIn("未提交改动", reason)

    def test_precheck_passes_clean(self):
        from zcode import update
        self.assertIsNone(update.precheck(self.root))

    def test_dry_run_prints_plan_only(self):
        """dry-run 打印全部步骤（含可选），不执行任何命令。"""
        import contextlib
        import io
        from unittest import mock
        from zcode import update
        buf = io.StringIO()
        with mock.patch.object(update, "_run", wraps=update._run) as m, \
                contextlib.redirect_stdout(buf):
            rc = update.run_update(dry_run=True, root=self.root)
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("git fetch origin", out)
        self.assertIn("npm link", out)          # package.json 存在 → 可选步列出
        self.assertIn("install.sh", out)
        m.assert_not_called()                    # 零执行

    def test_update_success_sequence(self):
        """成功路径：按序执行各步骤，末尾打印版本提示。"""
        import contextlib
        import io
        from unittest import mock
        from zcode import update
        # 序列: status → fetch → rev-list(有更新) → pull → pip → npm → install.sh → log
        seq = [(0, [])] * 2 + [(0, ["3"])] + [(0, [])] * 4 + [(0, ["abc123 提交"])]
        buf = io.StringIO()
        with mock.patch.object(update, "_run", side_effect=seq) as m, \
                contextlib.redirect_stdout(buf):
            rc = update.run_update(dry_run=False, root=self.root)
        self.assertEqual(rc, 0)
        cmds = [call.args[0][0:2] for call in m.call_args_list]
        self.assertEqual(cmds[1], ["git", "fetch"])
        self.assertEqual(cmds[3], ["git", "pull"])
        calls = [call.args[0] for call in m.call_args_list]
        self.assertTrue(any(c[:2] == [sys.executable, "-m"] and c[2] == "pip" for c in calls))
        self.assertIn("已更新", buf.getvalue())

    def test_update_already_latest(self):
        """fetch 后无新提交 → 提示已是最新并退出，不执行重装步骤。"""
        import contextlib
        import io
        from unittest import mock
        from zcode import update
        buf = io.StringIO()
        # 序列: status → fetch → rev-list(=0 无更新)
        with mock.patch.object(update, "_run", side_effect=[(0, []), (0, []), (0, ["0"])]) as m, \
                contextlib.redirect_stdout(buf):
            rc = update.run_update(dry_run=False, root=self.root)
        self.assertEqual(rc, 0)
        self.assertIn("已是最新", buf.getvalue())
        cmds = [call.args[0][0:2] for call in m.call_args_list]
        self.assertNotIn(["git", "pull"], cmds)  # 不执行重装步骤

    def test_update_failure_stops_with_guidance(self):
        """中间步骤失败 → UpdateError 含失败步骤与已完成列表。"""
        from unittest import mock
        from zcode import update
        # 序列: status → fetch → rev-list(有更新) → pull(1 失败)
        with mock.patch.object(update, "_run", side_effect=[(0, []), (0, []), (0, ["3"]), (1, ["conflict!"])]):
            with self.assertRaises(update.UpdateError) as ctx:
                update.run_update(dry_run=False, root=self.root)
        msg = str(ctx.exception)
        self.assertIn("git pull", msg)       # 失败步骤
        self.assertIn("已完成: git fetch origin", msg)  # 已完成列表
        self.assertIn("重跑 zcode update", msg)         # 恢复指引
