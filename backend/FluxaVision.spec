# -*- mode: python ; coding: utf-8 -*-
"""
FluxAvision 客流统计系统 - PyInstaller 打包配置

使用方法:
  cd backend
  pyinstaller FluxaVision.spec

输出:
  dist/FluxAvision/  — 包含 exe 和所有依赖的目录
"""
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 路径配置
BACKEND_DIR = os.path.dirname(os.path.abspath(SPEC))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
FRONTEND_BUILD = os.path.join(BACKEND_DIR, 'frontend-build')

# OpenCV DLL 收集
# collect_dynamic_libs 只收集标准加载的 DLL，FFmpeg 是 OpenCV 运行时动态加载的，
# 必须手动定位并加入，否则 VideoCapture(RTSP) 会永久卡住
import importlib.util as _cv2_ilu
import glob as _cv2_glob
_cv2_spec = _cv2_ilu.find_spec('cv2')
if _cv2_spec is None:
    raise RuntimeError('cv2 未安装，请先 pip install opencv-python-headless')
_cv2_dir = os.path.dirname(_cv2_spec.origin) if _cv2_spec.origin else list(_cv2_spec.submodule_search_locations)[0]
# 收集 cv2 目录下所有 DLL（含 opencv_videoio_ffmpeg*_64.dll）
_cv2_bins = [(f, '.') for f in _cv2_glob.glob(os.path.join(_cv2_dir, '*.dll'))]
# 同时收集 cv2 包同级目录（site-packages 层）的 FFmpeg DLL（部分安装位置在此）
_site_pkg_dir = os.path.dirname(_cv2_dir)
_cv2_bins += [(f, '.') for f in _cv2_glob.glob(os.path.join(_site_pkg_dir, 'opencv_videoio_ffmpeg*.dll'))]

# 大华 NetSDK 安装路径（pip install 后自动定位）
import importlib.util as _ilu
import glob as _glob
_netsdk_spec = _ilu.find_spec('NetSDK')
if _netsdk_spec is None:
    raise RuntimeError('NetSDK 未安装，请先执行: pip install NetSDK-2.0.0.1-py3-none-win_amd64.whl')
# origin 对 namespace package 为 None，改用 submodule_search_locations
if _netsdk_spec.origin:
    NETSDK_DIR = os.path.dirname(_netsdk_spec.origin)
else:
    NETSDK_DIR = list(_netsdk_spec.submodule_search_locations)[0]
NETSDK_DLL_DIR = os.path.join(NETSDK_DIR, 'Libs', 'win64')
NETSDK_DLLS = _glob.glob(os.path.join(NETSDK_DLL_DIR, '*.dll'))
if not NETSDK_DLLS:
    raise RuntimeError(f'未找到 NetSDK DLL 文件，请检查路径: {NETSDK_DLL_DIR}')

# ==================== 分析配置 ====================
a = Analysis(
    # 入口文件（使用 launcher.py 作为入口，支持命令行参数）
    [os.path.join(BACKEND_DIR, 'launcher.py')],

    pathex=[BACKEND_DIR],

    # OpenCV FFmpeg DLL（RTSP 流依赖，必须打包否则 VideoCapture 卡死）
    binaries=[
        *_cv2_bins,
        *[(dll, 'NetSDK/Libs/win64') for dll in NETSDK_DLLS],
    ],

    # 需要打包的数据文件
    datas=[
        # 静态前端文件（index.html, _next/, public/）
        (FRONTEND_BUILD, 'static'),
        # 应用图标（托盘图标、桌面快捷方式）
        (os.path.join(BACKEND_DIR, 'assets', 'icon.ico'), 'assets'),
        (os.path.join(BACKEND_DIR, 'assets', 'logo.png'), 'assets'),
        # 大华 NetSDK 整个目录（含 py 文件 + Libs/win64/*.dll）
        # 必须整体放入 datas 保持目录结构，SDK_Struct.py 用 __file__ 拼路径加载 DLL
        (NETSDK_DIR, 'NetSDK'),
        # cv2 整个包目录（含 .pyd 扩展 + haarcascades 等数据文件）
        (_cv2_dir, 'cv2'),
        # numpy（cv2 运行时强依赖，不能在 excludes 里排除）
        *collect_data_files('numpy'),
    ],

    hiddenimports=[
        # ── FastAPI ──────────────────────────────────────────────────────────
        'fastapi',
        'fastapi.applications',
        'fastapi.background',
        'fastapi.concurrency',
        'fastapi.datastructures',
        'fastapi.dependencies',
        'fastapi.dependencies.models',
        'fastapi.dependencies.utils',
        'fastapi.encoders',
        'fastapi.exception_handlers',
        'fastapi.exceptions',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'fastapi.openapi',
        'fastapi.openapi.constants',
        'fastapi.openapi.docs',
        'fastapi.openapi.models',
        'fastapi.openapi.utils',
        'fastapi.param_functions',
        'fastapi.params',
        'fastapi.requests',
        'fastapi.responses',
        'fastapi.routing',
        'fastapi.security',
        'fastapi.security.api_key',
        'fastapi.security.http',
        'fastapi.security.oauth2',
        'fastapi.security.open_id_connect_url',
        'fastapi.staticfiles',
        'fastapi.templating',
        'fastapi.testclient',
        'fastapi.types',
        'fastapi.utils',

        # ── Starlette (FastAPI 底层) ─────────────────────────────────────────
        'starlette',
        'starlette.applications',
        'starlette.background',
        'starlette.concurrency',
        'starlette.config',
        'starlette.convertors',
        'starlette.datastructures',
        'starlette.exceptions',
        'starlette.formparsers',
        'starlette.middleware',
        'starlette.middleware.base',
        'starlette.middleware.cors',
        'starlette.middleware.gzip',
        'starlette.middleware.httpsredirect',
        'starlette.middleware.sessions',
        'starlette.middleware.trustedhost',
        'starlette.middleware.wsgi',
        'starlette.requests',
        'starlette.responses',
        'starlette.routing',
        'starlette.schemas',
        'starlette.staticfiles',
        'starlette.status',
        'starlette.templating',
        'starlette.testclient',
        'starlette.types',
        'starlette.websockets',

        # ── Uvicorn ──────────────────────────────────────────────────────────
        'uvicorn',
        'uvicorn.config',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.main',
        'uvicorn.middleware',
        'uvicorn.middleware.asgi2',
        'uvicorn.middleware.message_logger',
        'uvicorn.middleware.proxy_headers',
        'uvicorn.middleware.wsgi',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.protocols.websockets.wsproto_impl',
        'uvicorn.lifespan',
        'uvicorn.lifespan.off',
        'uvicorn.lifespan.on',
        'uvicorn.server',
        'uvicorn.supervisors',
        'uvicorn.supervisors.basereload',
        'uvicorn.supervisors.multiprocess',
        'uvicorn.supervisors.statreload',
        'uvicorn.supervisors.watchfilesreload',
        'uvicorn.workers',

        # ── pydantic ─────────────────────────────────────────────────────────
        'pydantic',
        'pydantic.v1',
        'pydantic_core',
        'pydantic.networks',
        'pydantic.types',
        'pydantic.validators',
        'pydantic.fields',
        'pydantic.main',
        'pydantic.dataclasses',

        # ── anyio ────────────────────────────────────────────────────────────
        'anyio',
        'anyio._backends._asyncio',
        'anyio._backends._trio',
        'anyio.abc',
        'anyio.from_thread',
        'anyio.lowlevel',
        'anyio.streams',
        'anyio.streams.memory',

        # ── h11 (HTTP/1.1) ───────────────────────────────────────────────────
        'h11',
        'h11._connection',
        'h11._events',
        'h11._headers',
        'h11._readers',
        'h11._receivebuffer',
        'h11._state',
        'h11._util',
        'h11._writers',

        # ── python-multipart ─────────────────────────────────────────────────
        'multipart',
        'python_multipart',

        # ── SQLAlchemy ───────────────────────────────────────────────────────
        'sqlalchemy',
        'sqlalchemy.sql.default_comparator',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.dialects.sqlite.pysqlite',
        'sqlalchemy.ext.asyncio',

        # ── cryptography / field_crypto ──────────────────────────────────────
        'field_crypto',
        'cryptography',
        'cryptography.hazmat.backends.openssl',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.primitives.ciphers.algorithms',
        'cryptography.hazmat.primitives.ciphers.modes',
        'cryptography.hazmat.primitives.padding',

        # ── 应用路由模块（显式列出防止遗漏）────────────────────────────────────
        'routers',
        'routers.auth',
        'routers.devices',
        'routers.traffic',
        'routers.traffic_history',
        'routers.traffic_dashboard',
        'routers.traffic_collector',
        'routers.settings',
        'routers.large_screen',
        'routers.large_screen_templates',
        'routers.license',
        'routers.seed',
        'routers.device_id',
        'routers.device_status',
        'routers.stream',

        # ── numpy（cv2 强依赖）────────────────────────────────────────────────
        'numpy',
        'numpy.core',
        'numpy.core._multiarray_umath',
        'numpy.core._multiarray_tests',
        'numpy.lib',
        'numpy.linalg',
        'numpy.fft',
        'numpy.random',

        # ── 大华 NetSDK ───────────────────────────────────────────────────────
        'NetSDK',
        'NetSDK.NetSDK',
        'NetSDK.SDK_Callback',
        'NetSDK.SDK_Struct',
        'NetSDK.netsdk',

        # ── comtypes（桌面快捷方式创建）────────────────────────────────────────
        'comtypes',
        'comtypes.client',
        'comtypes.server',

        # ── 其他 ─────────────────────────────────────────────────────────────
        'email.mime.multipart',
        'email.mime.text',
        'logging.handlers',
    ],

    hookspath=[],
    hooksconfig={},

    runtime_hooks=[],

    excludes=[
        'tkinter',
        'matplotlib',
        # 'numpy',  # cv2 依赖 numpy，不能排除
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
    name='FluxAvision',
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
    icon=os.path.join(BACKEND_DIR, 'assets', 'icon.ico'),
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
    name='FluxAvision',
)
