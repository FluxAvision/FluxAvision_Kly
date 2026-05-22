"""
FluxaVision 客流统计系统 - Python 后端主入口

打包模式：
  - 开发模式: Python后端(8080) + Next.js前端(3000)，通过 rewrites 代理 API
  - 生产模式(exe): Python后端同时提供 API 和静态前端文件，单进程运行

技术栈：
  - FastAPI (高性能异步Web框架)
  - SQLite3 + AES-256 字段加密 (cryptography)
  - SQLAlchemy (ORM)
  - Uvicorn (ASGI服务器)

安全特性：
  - 数据库使用 AES-256 字段级透明加密（敏感字段自动加解密）
  - 加密密钥绑定硬件指纹，防止数据库被拷贝到其他机器使用
  - 密钥文件使用二次AES加密存储
"""
import logging
import sys
import os
import threading
from contextlib import asynccontextmanager

# 将 backend 目录加入 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from config import API_HOST, API_PORT, CORS_ORIGINS, BASE_DIR, get_static_dir
from database import init_database
from utils import error_response
from version import get_version

# 读取当前版本号
APP_VERSION = get_version()

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("FluxaVision")


# ==================== 生命周期管理 ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭生命周期管理"""
    # ── 启动 ──
    logger.info("=" * 60)
    logger.info(f"  FluxaVision 客流统计系统 v{APP_VERSION}")
    logger.info("  数据库加密: SQLite3 + AES-256 字段加密")
    logger.info("  视频流: RTSP → OpenCV MJPEG")
    logger.info("=" * 60)

    try:
        engine = init_database()
        logger.info("✓ 数据库初始化完成 (AES-256 字段加密)")
    except Exception as e:
        logger.error(f"✗ 数据库初始化失败: {e}")
        raise

    # 启动视频流管理器
    from stream_manager import stream_manager
    stream_manager.start()
    logger.info("✓ 视频流管理器已启动 (OpenCV MJPEG)")

    # 初始化内置大屏模板
    try:
        from routers.large_screen_templates import seed_builtin_templates
        seed_builtin_templates()
    except Exception as e:
        logger.warning(f"○ 内置大屏模板初始化失败: {e}")

    # 自动启动所有大华设备的客流采集
    try:
        from dahua_collector import dahua_collector
        if dahua_collector.available:
            dahua_collector.start_all_from_db()
            logger.info("✓ 大华SDK客流采集服务已启动")
        else:
            logger.info("○ 大华NetSDK不可用 (非Windows环境或未安装)")
    except Exception as e:
        logger.warning(f"○ 大华SDK启动失败: {e}")

    # 挂载静态文件
    has_static = _mount_static_files()
    if has_static:
        logger.info(f"✓ 静态前端已挂载: http://{API_HOST}:{API_PORT}")
    else:
        logger.info("✓ API模式启动: http://{API_HOST}:{API_PORT}")

    logger.info("=" * 60)

    yield  # 应用运行中...

    # ── 关闭 ──
    from stream_manager import stream_manager
    stream_manager.stop()
    logger.info("✓ 视频流管理器已停止")

    try:
        from dahua_collector import dahua_collector
        dahua_collector.stop_all()
        logger.info("✓ 客流采集器已停止")
    except Exception:
        pass


# ==================== FastAPI 应用 ====================
app = FastAPI(
    title="FluxAvision 客流统计系统",
    description="基于 Python FastAPI + SQLite3 + AES-256 字段加密的后端API",
    version=APP_VERSION,
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

# CORS 中间件配置
cors_origins = [origin.strip() for origin in CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 全局异常处理 ====================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "服务器内部错误"},
    )


# ==================== 注册 API 路由 ====================
from routers import (
    auth_router,
    devices_router,
    device_id_router,
    device_status_router,
    traffic_router,
    traffic_history_router,
    traffic_dashboard_router,
    device_push_router,
    traffic_collector_router,
    traffic_stats_router,
    settings_router,
    large_screen_router,
    large_screen_templates_router,
    license_router,
    seed_router,
    stream_router,
)

app.include_router(auth_router)
app.include_router(devices_router)
app.include_router(device_id_router)
app.include_router(device_status_router)
app.include_router(traffic_router)
app.include_router(traffic_history_router)
app.include_router(traffic_dashboard_router)
app.include_router(settings_router)
app.include_router(large_screen_router)
app.include_router(large_screen_templates_router)
app.include_router(license_router)
app.include_router(seed_router)
app.include_router(stream_router)
app.include_router(traffic_collector_router)
app.include_router(traffic_stats_router)
app.include_router(device_push_router)


# ==================== 健康检查 ====================
@app.get("/api/health")
async def health_check():
    return {"success": True, "message": "FluxaVision 后端运行正常", "version": APP_VERSION}


# ==================== 静态前端服务 ====================
def _mount_static_files():
    """
    挂载静态前端文件。

    打包模式（exe）: 从 PyInstaller 打包的 static/ 目录提供前端文件
    开发模式: 不挂载，由 Next.js dev server 提供前端
    """
    static_dir = get_static_dir()
    if not static_dir or not os.path.isdir(static_dir):
        logger.info("未找到静态前端文件，运行纯API模式（开发模式）")
        return False

    logger.info(f"挂载静态前端文件: {static_dir}")

    # 挂载 Vite assets/ 目录（JS/CSS/字体等）
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="vite_assets")

    # 挂载 public 子目录（如果存在）
    public_dir = os.path.join(static_dir, "public") if os.path.isdir(os.path.join(static_dir, "public")) else None
    if public_dir:
        app.mount("/public", StaticFiles(directory=public_dir), name="public_static")

    # favicon.ico（Vite 将 public/ 内容复制到构建根目录，也检查 public/ 子目录）
    favicon_path = os.path.join(static_dir, "favicon.ico")
    if not os.path.exists(favicon_path) and public_dir:
        favicon_path = os.path.join(public_dir, "favicon.ico")
    if os.path.exists(favicon_path):
        @app.get("/favicon.ico")
        async def favicon():
            return FileResponse(favicon_path)

    # logo.png / logo.svg（检查根目录，再检查 public/ 子目录）
    for logo_name in ["logo.png", "logo.svg"]:
        logo_path = os.path.join(static_dir, logo_name)
        if not os.path.exists(logo_path) and public_dir:
            logo_path = os.path.join(public_dir, logo_name)
        if os.path.exists(logo_path):
            path = logo_path

            @app.get(f"/{logo_name}")
            async def logo_fn():
                return FileResponse(path)

            break

    # SPA fallback
    index_html_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_html_path):
        @app.get("/{path:path}")
        async def spa_catch_all(request: Request, path: str):
            if path.startswith("api/"):
                return JSONResponse(status_code=404, content={"success": False, "message": "API not found"})
            return FileResponse(index_html_path)

    return True


# ==================== 直接运行 ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level="info",
    )
