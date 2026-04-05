# -*- mode: python ; coding: utf-8 -*-
"""
FluxaVision 客流统计系统 - PyInstaller 打包配置

使用方法:
  cd backend
  pyinstaller FluxaVision.spec

输出:
  dist/FluxaVision/  — 包含 exe 和所有依赖的目录
"""
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 路径配置
BACKEND_DIR = os.path.dirname(os.path.abspath(SPEC))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
FRONTEND_BUILD = os.path.join(BACKEND_DIR, 'frontend-build')

# ==================== 分析配置 ====================
a = Analysis(
    # 入口文件（使用 launcher.py 作为入口，支持命令行参数）
    [os.path.join(BACKEND_DIR, 'launcher.py')],

    pathex=[BACKEND_DIR],

    binaries=[],

    # 需要打包的数据文件
    datas=[
        # 静态前端文件（index.html, _next/, public/）
        (FRONTEND_BUILD, 'static'),
    ],

    hiddenimports=[
        # FastAPI 和 Uvicorn 依赖
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'multipart',
        'anyio._backends._asyncio',

        # SQLAlchemy
        'sqlalchemy.sql.default_comparator',
        'sqlalchemy.dialects.sqlite',

        # sqlcipher3
        'sqlcipher3',
        'sqlcipher3.dbapi2',

        # cryptography
        'cryptography',
        'cryptography.hazmat.backends.openssl',

        # 其他
        'email.mime.multipart',
    ],

    hookspath=[],
    hooksconfig={},

    runtime_hooks=[],

    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'pytest',
        'IPython',
        'jupyter',
        'notebook',
        'setuptools',
        'pip',
    ],

    noarchive=False,
    optimize=0,
)

# ==================== PYZ 压缩 ====================
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# ==================== EXE 配置 ====================
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FluxaVision',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # 无控制台窗口（静默后台运行）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 应用图标（Windows .ico 文件）
    icon=os.path.join(BACKEND_DIR, 'assets', 'icon.ico') if os.path.exists(os.path.join(BACKEND_DIR, 'assets', 'icon.ico')) else None,
)

# ==================== 目录输出 ====================
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FluxaVision',
)
