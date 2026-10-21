"""先配置 Compass 的 Git 本地排除，再按需创建缺失的通用骨架。"""

from __future__ import annotations

import argparse
import json
import stat
import subprocess
import sys
from pathlib import Path


SCAFFOLD = Path(__file__).resolve().parents[1] / "assets" / "scaffold"
FILES = (
    Path("README.md"),
    Path("constraints.md"),
    Path("knowledge/README.md"),
    Path("knowledge/project-specific/README.md"),
    Path("requirements/README.md"),
)


def _git(project: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(project), *arguments],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def prepare_local_ignore(project: Path) -> dict[str, str]:
    """只修改 Git 提供的本地 exclude 文件，不修改共享规则或索引。"""
    root = project.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"项目目标不是目录：{root}")
    try:
        location = _git(root, "rev-parse", "--show-toplevel")
    except FileNotFoundError as error:
        raise ValueError("找不到 Git，无法确认或设置本地忽略；请先说明环境或手动处理。") from error
    if location.returncode:
        if "not a git repository" in location.stderr.lower():
            return {"status": "not_git", "project": str(root)}
        raise ValueError(f"无法识别 Git 工作区：{location.stderr.strip()}")

    repository = Path(location.stdout.strip()).resolve(strict=True)
    relative = (root / "docs" / "ChiChengDocs").relative_to(repository).as_posix()
    tracked = _git(repository, "ls-files", "-z", "--", f":(literal){relative}")
    if tracked.returncode:
        raise ValueError(f"无法检查资料目录的跟踪状态：{tracked.stderr.strip()}")
    if tracked.stdout:
        raise ValueError(
            f"{relative} 中已有 Git 跟踪或暂存的内容，本地忽略不能使其停止跟踪；"
            "未修改索引或共享 .gitignore，请先由用户决定如何处理。"
        )

    exclude_path = _git(repository, "rev-parse", "--git-path", "info/exclude")
    if exclude_path.returncode:
        raise ValueError(f"无法定位 Git 本地排除文件：{exclude_path.stderr.strip()}")
    exclude = Path(exclude_path.stdout.strip())
    if not exclude.is_absolute():
        exclude = repository / exclude
    exclude = exclude.resolve()

    # 路径来自用户选择的项目，转义目录名中可能具有匹配含义的字符。
    escaped = "".join("\\" + char if char in "\\*?[]" else char for char in relative)
    pattern = f"/{escaped}/"
    encoded = pattern.encode("utf-8")
    existing = exclude.read_bytes() if exclude.exists() else b""
    added = encoded not in existing.splitlines()
    if added:
        newline = b"\r\n" if b"\r\n" in existing else b"\n"
        separator = newline if existing and not existing.endswith(b"\n") else b""
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("ab") as output:
            output.write(separator + encoded + newline)

    effective = _git(repository, "check-ignore", "--no-index", "-q", "--", relative + "/")
    if effective.returncode:
        raise ValueError(
            f"已保留本地规则 {pattern}，但尚未验证为有效忽略；"
            "请检查规则覆盖或 Git 错误，不自动修改共享 .gitignore。"
        )
    return {
        "status": "configured" if added else "already_configured",
        "repository": str(repository), "exclude_file": str(exclude), "pattern": pattern,
    }


def _is_link(path: Path) -> bool:
    """同时识别符号链接和 Windows 目录联接，避免写入其他实际位置。"""
    if path.is_symlink():
        return True
    if not path.exists():
        return False
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def initialize(project: Path, scaffold: Path = SCAFFOLD) -> dict[str, object]:
    """先检查全部目标，再独占创建；保留已有文件的原始字节。"""
    root = project.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"项目目标不是目录：{root}")

    docs_root = root / "docs" / "ChiChengDocs"
    prepared = []
    for relative in FILES:
        content = (scaffold / relative).read_bytes()
        destination = docs_root / relative
        # 在创建任何目录之前检查各个文件的完整路径。
        current = root
        for part in destination.relative_to(root).parts[:-1]:
            current = current / part
            if _is_link(current):
                raise ValueError(f"目标路径含链接或目录联接，请明确实际目录：{current}")
            if current.exists() and not current.is_dir():
                raise ValueError(f"预期目录被文件占用：{current}")
        if _is_link(destination):
            raise ValueError(f"目标文件为链接，请先明确其用途：{destination}")
        if destination.exists() and not destination.is_file():
            raise ValueError(f"预期文件被其他对象占用：{destination}")
        destination.resolve().relative_to(root)
        prepared.append((relative, destination, content))

    local_ignore = prepare_local_ignore(root)
    created = []
    preserved = []
    for relative, destination, content in prepared:
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with destination.open("xb") as output:
                output.write(content)
        except FileExistsError:
            # 也保留在预检查之后由另一个正常初始化创建的文件。
            if _is_link(destination) or not destination.is_file():
                raise ValueError(f"目标类型在初始化期间变化，请检查：{destination}")
            preserved.append(relative.as_posix())
        else:
            created.append(relative.as_posix())

    return {
        "project": str(root),
        "docs_root": str(docs_root),
        "created": created,
        "preserved": preserved,
        "local_ignore": local_ignore,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="配置 Git 本地排除，并按需创建 Compass 缺失骨架。")
    parser.add_argument("--project", required=True, type=Path, help="已存在的项目目录")
    parser.add_argument("--prepare-only", action="store_true", help="只准备本地忽略，不创建资料骨架")
    args = parser.parse_args()
    try:
        result = prepare_local_ignore(args.project) if args.prepare_only else initialize(args.project)
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
