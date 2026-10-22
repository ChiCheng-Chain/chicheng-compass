"""只读发现当前项目或目录下的项目及 Compass 入口，不初始化或修改配置。"""

from __future__ import annotations

import argparse
from collections import deque
import json
from pathlib import Path
import stat
import sys


SKIP = {
    "node_modules", "vendor", "venv", ".venv", "__pycache__", "dist", "build",
    "target", "coverage", "backups", "backup", "fixtures", "tests", "docs",
}
MANIFESTS = ("package.json", "pyproject.toml", "pom.xml", "go.mod", "Cargo.toml")


def _linked(path: Path) -> bool:
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    return path.is_symlink() or bool(
        attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _plain(root: Path, relative: str) -> Path | None:
    """默认入口的每一层都留在项目内，不跟随链接或目录联接。"""
    current = root
    for part in Path(relative).parts:
        current = current / part
        if not current.exists() or _linked(current):
            return None
    return current


def _describe(root: Path) -> dict[str, object] | None:
    git = _plain(root, ".git")
    markers = [name for name in MANIFESTS if (root / name).is_file()]
    entry = _plain(root, "docs/ChiChengDocs/README.md")
    knowledge = _plain(root, "docs/ChiChengDocs/knowledge/README.md")
    if not git and not markers and not entry and not knowledge:
        return None
    readme = _plain(root, "README.md")
    return {
        "name": root.name,
        "project": str(root),
        "evidence": ([".git"] if git else []) + markers
        + (["Compass entry"] if entry or knowledge else []),
        "compass_entry": str(entry) if entry and entry.is_file() else None,
        "knowledge_entry": str(knowledge) if knowledge and knowledge.is_file() else None,
        "readme": str(readme) if readme and readme.is_file() else None,
        "knowledge_status": "entry_found_unverified" if knowledge else "not_found",
    }


def discover(directory: Path, *, max_depth: int = 3, max_directories: int = 2000) -> dict:
    if max_depth < 0 or max_directories < 1:
        raise ValueError("扫描深度不能为负，目录上限必须大于零")
    root = directory.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"起点不是目录：{root}")

    # 从项目内部调用时优先选择最近 Git 根，不把 backend 等子包分成另一个项目。
    for ancestor in (root, *root.parents):
        marker = _plain(ancestor, ".git")
        if marker and (marker.is_file() or marker.is_dir()):
            return {
                "directory": str(root), "mode": "project",
                "projects": [_describe(ancestor)], "incomplete": False, "warnings": [],
            }

    for ancestor in (root, *root.parents):
        current = _describe(ancestor)
        if current:
            return {
                "directory": str(root), "mode": "project", "projects": [current],
                "incomplete": False, "warnings": [],
            }

    queue = deque([(root, 0)])
    projects = []
    warnings = []
    visited = 0
    incomplete = False
    while queue:
        if visited >= max_directories:
            warnings.append("达到目录扫描上限；未扫描部分不能认定没有项目")
            incomplete = True
            break
        folder, depth = queue.popleft()
        visited += 1
        try:
            candidate = _describe(folder)
            if candidate:
                projects.append(candidate)
                # 仓库内部包、样例和嵌套目录不自动扩成独立项目。
                continue
            children = sorted(
                (path for path in folder.iterdir()
                 if not path.name.startswith(".") and path.name.lower() not in SKIP
                 and not _linked(path) and path.is_dir()),
                key=lambda path: path.name.casefold(),
            )
            if depth >= max_depth:
                if children:
                    warnings.append(f"达到深度限制：{folder}；需要时指定更具体的起点")
                    incomplete = True
                continue
            queue.extend((path, depth + 1) for path in children)
        except OSError as error:
            warnings.append(f"无法检查 {folder}：{error}")
            incomplete = True
    return {
        "directory": str(root), "mode": "workspace" if projects else "empty",
        "projects": projects, "incomplete": incomplete, "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="只读发现项目及各自的知识入口，不写入文件。")
    parser.add_argument("--directory", required=True, type=Path, help="本次工作目录，不是Skill安装目录")
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--max-directories", type=int, default=2000)
    args = parser.parse_args()
    try:
        result = discover(args.directory, max_depth=args.max_depth,
                          max_directories=args.max_directories)
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
