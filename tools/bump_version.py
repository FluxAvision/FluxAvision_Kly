#!/usr/bin/env python3
"""
版本号自动递增脚本 — bump_version.py

用法：
    python tools/bump_version.py --part=patch    # 递增修订号: 2.1.0 -> 2.1.1
    python tools/bump_version.py --part=minor    # 递增次版本号: 2.1.0 -> 2.2.0
    python tools/bump_version.py                  # 默认 --part=patch
    python tools/bump_version.py --commit         # 递增后自动 git add VERSION
    python tools/bump_version.py --part=minor --commit

说明：
    - 读取项目根目录的 VERSION 文件
    - 语义化版本号格式: X.Y.Z
    - --commit: 递增后自动 git add VERSION（用于钩子脚本）
"""

import argparse
import os
import re
import subprocess
import sys


def get_project_root() -> str:
    """获取项目根目录（脚本位于 tools/bump_version.py）"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_version(project_root: str) -> str:
    """读取 VERSION 文件"""
    version_path = os.path.join(project_root, "VERSION")
    try:
        with open(version_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"错误: 未找到 VERSION 文件 ({version_path})")
        sys.exit(1)


def write_version(project_root: str, version: str):
    """写入 VERSION 文件"""
    version_path = os.path.join(project_root, "VERSION")
    with open(version_path, "w", encoding="utf-8") as f:
        f.write(version + "\n")
    print(f"  VERSION: {version}")


def bump_version(version: str, part: str) -> str:
    """
    语义化版本递增
    - patch: X.Y.Z -> X.Y.(Z+1)
    - minor: X.Y.Z -> X.(Y+1).0
    """
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        print(f"错误: VERSION 格式无效 '{version}'，应为 X.Y.Z")
        sys.exit(1)

    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))

    if part == "patch":
        patch += 1
    elif part == "minor":
        minor += 1
        patch = 0
    else:
        print(f"错误: 未知的 --part 参数 '{part}'，可选: minor, patch")
        sys.exit(1)

    return f"{major}.{minor}.{patch}"


def git_add_version(project_root: str):
    """执行 git add VERSION"""
    try:
        result = subprocess.run(
            ["git", "add", "VERSION"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("  git add VERSION: OK")
        else:
            print(f"  git add VERSION 失败: {result.stderr.strip()}")
    except FileNotFoundError:
        print("  git add VERSION 失败: 未找到 git 命令")


def main():
    parser = argparse.ArgumentParser(description="递增项目版本号 (VERSION 文件)")
    parser.add_argument(
        "--part",
        choices=["minor", "patch"],
        default="patch",
        help="版本部分: minor (次版本) 或 patch (修订号, 默认)",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="递增后自动 git add VERSION",
    )
    args = parser.parse_args()

    project_root = get_project_root()
    print(f"项目根目录: {project_root}")

    old_version = read_version(project_root)
    print(f"当前版本:   {old_version}")

    new_version = bump_version(old_version, args.part)
    print(f"递增部分:   {args.part}")

    write_version(project_root, new_version)

    if args.commit:
        git_add_version(project_root)


if __name__ == "__main__":
    main()
