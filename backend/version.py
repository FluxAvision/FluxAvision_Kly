"""
版本管理模块 — 从项目根目录 VERSION 文件读取版本号

策略：
- 开发模式: 从 backend/ 上级目录（项目根）读取 VERSION
- 打包模式(exe): 从 exe 所在目录读取 VERSION
"""

import sys
import os


def _get_project_dir() -> str:
    """获取项目根目录（开发模式）或 exe 所在目录（打包模式）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        # backend/version.py -> backend/ -> 上级目录 = 项目根
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_version() -> str:
    """从 VERSION 文件读取当前版本号，失败时返回 '0.0.0'"""
    version_path = os.path.join(_get_project_dir(), "VERSION")
    try:
        with open(version_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"
