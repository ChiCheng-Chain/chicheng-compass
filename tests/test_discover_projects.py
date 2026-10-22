"""项目发现只读，不要求测试仓库执行真实 Git 或安装第三方工具。"""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/chicheng-compass/scripts/discover_projects.py"
SPEC = importlib.util.spec_from_file_location("compass_discover", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DiscoverProjectsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "父目录 with spaces"
        self.root.mkdir()

    def project(self, name, *, git_file=False):
        path = self.root / name
        path.mkdir(parents=True)
        if git_file:
            (path / ".git").write_text("gitdir: elsewhere", encoding="utf-8")
        else:
            (path / ".git").mkdir()
        return path

    def test_current_git_project_wins_over_inner_package(self):
        project = self.project("业务项目")
        package = project / "backend"
        package.mkdir()
        (package / "package.json").write_text("{}", encoding="utf-8")
        result = MODULE.discover(package)
        self.assertEqual("project", result["mode"])
        self.assertEqual([str(project)], [item["project"] for item in result["projects"]])

    def test_parent_lists_independent_projects_and_separate_knowledge(self):
        first = self.project("first")
        second = self.project("second", git_file=True)
        kb = first / "docs/ChiChengDocs/knowledge/README.md"
        kb.parent.mkdir(parents=True)
        kb.write_text("项目知识尚未建立。", encoding="utf-8")
        before = sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*"))
        result = MODULE.discover(self.root)
        self.assertEqual("workspace", result["mode"])
        self.assertEqual([str(first), str(second)], [item["project"] for item in result["projects"]])
        self.assertEqual(str(kb), result["projects"][0]["knowledge_entry"])
        self.assertEqual("entry_found_unverified", result["projects"][0]["knowledge_status"])
        self.assertIsNone(result["projects"][1]["knowledge_entry"])
        self.assertEqual(before, sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*")))
        self.assertEqual("项目知识尚未建立。", kb.read_text(encoding="utf-8"))
        self.assertFalse((self.root / "docs").exists())

    def test_non_git_project_from_internal_directory(self):
        (self.root / "pyproject.toml").write_text("", encoding="utf-8")
        internal = self.root / "src" / "core"
        internal.mkdir(parents=True)
        result = MODULE.discover(internal)
        self.assertEqual(str(self.root), result["projects"][0]["project"])
        self.assertFalse((self.root / ".git").exists())

    def test_single_child_is_not_the_parent_project(self):
        project = self.project("only")
        result = MODULE.discover(self.root)
        self.assertEqual("workspace", result["mode"])
        self.assertEqual(str(project), result["projects"][0]["project"])
        self.assertFalse(result["incomplete"])

    def test_skips_backups_dependencies_samples_and_hidden_worktrees(self):
        real = self.project("real")
        for name in ("backups/copy", "node_modules/lib", "tests/fixtures/sample", ".worktrees/branch"):
            self.project(name)
        result = MODULE.discover(self.root)
        self.assertEqual([str(real)], [item["project"] for item in result["projects"]])

    def test_depth_and_count_limits_report_incomplete_results(self):
        self.project("wrapper/deeper/project")
        depth = MODULE.discover(self.root, max_depth=1)
        self.assertTrue(depth["incomplete"])
        self.assertEqual([], depth["projects"])
        count = MODULE.discover(self.root, max_directories=1)
        self.assertTrue(count["incomplete"])
        self.assertEqual([], count["projects"])

    def test_missing_or_invalid_directory_and_limits(self):
        with self.assertRaises(OSError):
            MODULE.discover(self.root / "absent")
        with self.assertRaises(ValueError):
            MODULE.discover(self.root, max_depth=-1)
        with self.assertRaises(ValueError):
            MODULE.discover(self.root, max_directories=0)

    def test_cli_read_only_does_not_use_its_installation_directory(self):
        project = self.project("candidate")
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPT), "--directory", str(self.root)],
            cwd=self.base, capture_output=True, text=True, encoding="utf-8", check=True,
        )
        output = json.loads(result.stdout)
        self.assertEqual(str(project), output["projects"][0]["project"])
        self.assertEqual(str(self.root), output["directory"])
        self.assertFalse((self.root / "docs").exists())

    @unittest.skipUnless(sys.platform == "win32", "仅Windows有目录联接")
    def test_windows_junction_is_not_followed(self):
        outside = self.base / "外部项目"
        outside.mkdir()
        (outside / ".git").mkdir()
        link = self.root / "alias"
        environment = os.environ.copy()
        environment["COMPASS_DISCOVERY_LINK"] = str(link)
        environment["COMPASS_DISCOVERY_TARGET"] = str(outside)
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "New-Item -ItemType Junction -Path $env:COMPASS_DISCOVERY_LINK "
             "-Target $env:COMPASS_DISCOVERY_TARGET -ErrorAction Stop | Out-Null"],
            env=environment, capture_output=True, check=True,
        )
        self.addCleanup(link.rmdir)
        self.assertEqual([], MODULE.discover(self.root)["projects"])


if __name__ == "__main__":
    unittest.main()
