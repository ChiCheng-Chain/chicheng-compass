"""显式初始化 Compass 资料区，只创建缺失的通用骨架文件。"""

from __future__ import annotations

import argparse
import json
import stat
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
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="创建 Compass 缺失骨架，保留已有资料。")
    parser.add_argument("--project", required=True, type=Path, help="已存在的项目目录")
    args = parser.parse_args()
    try:
        result = initialize(args.project)
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
