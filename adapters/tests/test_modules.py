"""workflow.py / handoff.py / marketplace.py / profile.py 单元测试。"""
from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
