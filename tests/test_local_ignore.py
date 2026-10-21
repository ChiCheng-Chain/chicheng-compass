"""用隔离 Git 仓库验证本地忽略，不修改用户或系统 Git 配置。"""

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/chicheng-compass/scripts/init_workspace.py"
SPEC = importlib.util.spec_from_file_location("compass_workspace", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@unittest.skipUnless(shutil.which("git"), "需要 Git 才能验证本地排除")
class LocalIgnoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / "项目 with spaces"
        self.project.mkdir()
        self.git("init", "-q")
        empty_excludes = self.base / "empty-excludes"
        empty_excludes.write_bytes(b"")
        self.git("config", "core.excludesFile", str(empty_excludes))

    def git(self, *arguments, cwd=None, check=True):
        result = subprocess.run(
            ["git", "-C", str(cwd or self.project), *arguments],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if check and result.returncode:
            self.fail(f"Git {arguments} 失败：{result.stderr}")
        return result

    def test_init_ignores_generated_docs_during_normal_staging(self):
        shared = self.project / ".gitignore"
        shared.write_bytes(b"*.cache\r\n")
        result = MODULE.initialize(self.project)
        self.assertEqual("configured", result["local_ignore"]["status"])
        self.assertEqual("/docs/ChiChengDocs/", result["local_ignore"]["pattern"])
        self.assertEqual(b"*.cache\r\n", shared.read_bytes())
        self.git("add", "--all")
        tracked = self.git("ls-files", "-z").stdout.split("\0")
        self.assertFalse(any(path.startswith("docs/ChiChengDocs/") for path in tracked))

    def test_preserves_existing_exclude_and_does_not_repeat_pattern(self):
        exclude = self.project / ".git/info/exclude"
        original = b"# personal rules\r\n*.local"
        exclude.write_bytes(original)
        first = MODULE.prepare_local_ignore(self.project)
        once = exclude.read_bytes()
        second = MODULE.prepare_local_ignore(self.project)
        self.assertEqual("configured", first["status"])
        self.assertEqual("already_configured", second["status"])
        self.assertTrue(once.startswith(original + b"\r\n"))
        self.assertEqual(once, exclude.read_bytes())
        self.assertEqual(1, once.count(b"/docs/ChiChengDocs/"))

    def test_prepare_only_does_not_create_docs(self):
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPT), "--project", str(self.project), "--prepare-only"],
            capture_output=True, text=True, encoding="utf-8", check=True,
        )
        self.assertIn('"configured"', result.stdout)
        self.assertFalse((self.project / "docs").exists())

    def test_non_git_project_does_not_gain_git_metadata(self):
        plain = self.base / "ordinary-directory"
        plain.mkdir()
        result = MODULE.initialize(plain)
        self.assertEqual("not_git", result["local_ignore"]["status"])
        self.assertFalse((plain / ".git").exists())
        self.assertEqual(5, len(result["created"]))

    def test_tracked_docs_stop_init_without_removing_index_or_changing_exclude(self):
        note = self.project / "docs/ChiChengDocs/existing.md"
        note.parent.mkdir(parents=True)
        note.write_text("团队已跟踪文档", encoding="utf-8")
        self.git("add", "--", "docs/ChiChengDocs/existing.md")
        index_before = self.git("ls-files", "--stage", "-z").stdout
        exclude = self.project / ".git/info/exclude"
        exclude_before = exclude.read_bytes()
        with self.assertRaises(ValueError):
            MODULE.initialize(self.project)
        self.assertEqual(index_before, self.git("ls-files", "--stage", "-z").stdout)
        self.assertEqual(exclude_before, exclude.read_bytes())
        self.assertFalse((note.parent / "README.md").exists())
        self.assertEqual("团队已跟踪文档", note.read_text(encoding="utf-8"))

    def test_shared_negation_is_reported_without_changing_shared_rules(self):
        shared = self.project / ".gitignore"
        original = b"!/docs/ChiChengDocs/\n"
        shared.write_bytes(original)
        with self.assertRaises(ValueError):
            MODULE.initialize(self.project)
        self.assertEqual(original, shared.read_bytes())
        self.assertFalse((self.project / "docs").exists())

    def test_project_subdirectory_gets_only_its_own_exclude_pattern(self):
        subproject = self.project / "apps" / "api [test]"
        subproject.mkdir(parents=True)
        result = MODULE.prepare_local_ignore(subproject)
        self.assertEqual("/apps/api \\[test\\]/docs/ChiChengDocs/", result["pattern"])
        check = self.git("check-ignore", "-q", "--", "docs/ChiChengDocs/", check=False)
        self.assertEqual(1, check.returncode)

    def test_linked_worktree_uses_git_resolved_exclude_file(self):
        (self.project / "README.md").write_text("测试仓库", encoding="utf-8")
        self.git("add", "README.md")
        self.git("-c", "user.name=Compass Test", "-c", "user.email=compass@example.invalid",
                 "commit", "-qm", "测试基线")
        linked = self.base / "关联工作树"
        self.git("worktree", "add", "--detach", str(linked))
        self.assertTrue((linked / ".git").is_file())
        result = MODULE.initialize(linked)
        actual = Path(result["local_ignore"]["exclude_file"])
        self.assertEqual((self.project / ".git/info/exclude").resolve(), actual)
        self.git("add", "--all", cwd=linked)
        self.assertEqual("README.md\0", self.git("ls-files", "-z", cwd=linked).stdout)


if __name__ == "__main__":
    unittest.main()
