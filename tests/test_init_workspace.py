"""验证初始化的可观察行为；所有生成内容仅写入临时目录。"""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "skills" / "chicheng-compass"
SCRIPT = SKILL / "scripts" / "init_workspace.py"
SPEC = importlib.util.spec_from_file_location("compass_init", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InitWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / "陌生项目 with spaces"
        self.project.mkdir()
        self.docs = self.project / "docs" / "ChiChengDocs"

    def test_creates_scaffold_without_project_facts_or_tools(self):
        result = MODULE.initialize(self.project)
        actual = {
            path.relative_to(self.project).as_posix()
            for path in self.project.rglob("*")
            if path.is_file()
        }
        expected = {
            "docs/ChiChengDocs/README.md",
            "docs/ChiChengDocs/constraints.md",
            "docs/ChiChengDocs/knowledge/README.md",
            "docs/ChiChengDocs/knowledge/project-specific/README.md",
            "docs/ChiChengDocs/requirements/README.md",
        }
        self.assertEqual(expected, actual)
        self.assertEqual(5, len(result["created"]))
        self.assertEqual([], result["preserved"])
        for relative in MODULE.FILES:
            self.assertEqual(
                (SKILL / "assets" / "scaffold" / relative).read_bytes(),
                (self.docs / relative).read_bytes(),
            )

    def test_repeat_preserves_user_bytes_and_restores_only_missing_files(self):
        MODULE.initialize(self.project)
        modified = self.docs / "constraints.md"
        user_content = "# 我的约束\r\n\r\n已有规则原样保留。\r\n".encode("utf-8")
        modified.write_bytes(user_content)
        project_notes = self.docs / "knowledge" / "project-specific" / "README.md"
        project_content = "# 项目专属信息\n\n已有脚本说明和项目约束。\n".encode("utf-8")
        project_notes.write_bytes(project_content)
        missing = self.docs / "requirements" / "README.md"
        missing.unlink()
        result = MODULE.initialize(self.project)
        self.assertEqual(["requirements/README.md"], result["created"])
        self.assertEqual(4, len(result["preserved"]))
        self.assertEqual(user_content, modified.read_bytes())
        self.assertEqual(project_content, project_notes.read_bytes())
        repeated = MODULE.initialize(self.project)
        self.assertEqual([], repeated["created"])
        self.assertEqual(5, len(repeated["preserved"]))

    def test_team_rules_and_existing_docs_are_untouched(self):
        existing = {
            self.project / "AGENTS.md": b"team rules\r\n",
            self.project / "CLAUDE.md": b"@AGENTS.md\n",
            self.project / "docs" / "design.md": "团队设计".encode("utf-8"),
        }
        for path, content in existing.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        MODULE.initialize(self.project)
        for path, content in existing.items():
            self.assertEqual(content, path.read_bytes())

    def test_directory_conflict_is_found_before_any_scaffold_write(self):
        self.docs.mkdir(parents=True)
        (self.docs / "knowledge").write_text("已有文件", encoding="utf-8")
        with self.assertRaises(ValueError):
            MODULE.initialize(self.project)
        self.assertFalse((self.docs / "README.md").exists())
        self.assertFalse((self.docs / "constraints.md").exists())

    def test_file_destination_conflict_is_found_before_any_scaffold_write(self):
        (self.docs / "constraints.md").mkdir(parents=True)
        with self.assertRaises(ValueError):
            MODULE.initialize(self.project)
        self.assertFalse((self.docs / "README.md").exists())

    def test_missing_project_is_not_created(self):
        missing = self.base / "不存在的仓库"
        with self.assertRaises(OSError):
            MODULE.initialize(missing)
        self.assertFalse(missing.exists())

    def test_target_file_is_not_treated_as_project(self):
        target = self.base / "file"
        target.write_bytes(b"keep")
        with self.assertRaises(ValueError):
            MODULE.initialize(target)
        self.assertEqual(b"keep", target.read_bytes())

    def test_missing_template_does_not_leave_partial_output(self):
        incomplete = self.base / "incomplete-scaffold"
        incomplete.mkdir()
        (incomplete / "README.md").write_bytes(b"one template")
        with self.assertRaises(OSError):
            MODULE.initialize(self.project, incomplete)
        self.assertFalse((self.project / "docs").exists())

    def test_symlink_directory_does_not_redirect_output(self):
        elsewhere = self.base / "其他项目"
        elsewhere.mkdir()
        try:
            (self.project / "docs").symlink_to(elsewhere, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"当前环境不能创建符号链接：{error}")
        with self.assertRaises(ValueError):
            MODULE.initialize(self.project)
        self.assertEqual([], list(elsewhere.iterdir()))

    def test_parallel_initializations_preserve_complete_files(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(MODULE.initialize, [self.project, self.project]))
        self.assertEqual(5, sum(len(result["created"]) for result in results))
        for relative in MODULE.FILES:
            self.assertEqual(
                (SKILL / "assets" / "scaffold" / relative).read_bytes(),
                (self.docs / relative).read_bytes(),
            )

    @unittest.skipUnless(sys.platform == "win32", "仅 Windows 有目录联接")
    def test_windows_junction_does_not_redirect_output(self):
        elsewhere = self.base / "目录联接目标"
        elsewhere.mkdir()
        link = self.project / "docs"
        environment = os.environ.copy()
        environment["COMPASS_TEST_LINK"] = str(link)
        environment["COMPASS_TEST_TARGET"] = str(elsewhere)
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "New-Item -ItemType Junction -Path $env:COMPASS_TEST_LINK "
             "-Target $env:COMPASS_TEST_TARGET -ErrorAction Stop | Out-Null"],
            env=environment, check=True, capture_output=True,
        )
        self.addCleanup(link.rmdir)
        with self.assertRaises(ValueError):
            MODULE.initialize(self.project)
        self.assertEqual([], list(elsewhere.iterdir()))

    def test_copied_skill_works_outside_original_repo_and_working_directory(self):
        copied = self.base / "独立 Skill 副本"
        shutil.copytree(SKILL, copied, ignore=shutil.ignore_patterns("__pycache__"))
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(copied / "scripts" / "init_workspace.py"),
             "--project", str(self.project)],
            cwd=self.base, capture_output=True, text=True, encoding="utf-8", check=True,
        )
        output = json.loads(result.stdout)
        self.assertEqual(str(self.project.resolve()), output["project"])
        self.assertEqual(5, len(output["created"]))
        self.assertFalse((copied / "docs").exists())


if __name__ == "__main__":
    unittest.main()
