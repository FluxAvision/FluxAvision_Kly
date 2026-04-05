"""
FluxaVision 客流统计系统 - 入口启动器

这是 PyInstaller 打包的入口文件。
负责：解析命令行参数 → 初始化服务 → 启动后端 → 托盘图标
"""
import sys
import os

# ── PyInstaller console=False 模式下 stdout/stderr 为 None ──────────────────
# uvicorn 的 DefaultFormatter.__init__ 会调用 sys.stdout.isatty()，
# None 无此方法，直接抛 AttributeError → ValueError: Unable to configure formatter。
# 必须在所有 import 之前将其替换为可用的空流。
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w', encoding='utf-8')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w', encoding='utf-8')

# 确保 backend 目录在 Python 路径中
if getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.dirname(sys.executable))
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
import argparse
import threading


# ==================== 命令行参数解析 ====================
def parse_args():
    parser = argparse.ArgumentParser(description="FluxaVision 客流统计系统")
    parser.add_argument("--console", action="store_true", help="控制台模式（调试用）")
    parser.add_argument("--port", type=int, default=None, help="指定端口号")
    parser.add_argument("--install", action="store_true", help="安装开机自启动")
    parser.add_argument("--uninstall", action="store_true", help="卸载开机自启动")
    return parser.parse_args()


def main():
    args = parse_args()

    # 处理自启动安装/卸载
    if args.install:
        from windows_service import install_autostart
        install_autostart()
        return

    if args.uninstall:
        from windows_service import uninstall_autostart
        uninstall_autostart()
        return

    # 设置环境变量
    if args.port:
        os.environ["API_PORT"] = str(args.port)

    # 单实例检查
    from windows_service import check_single_instance
    if not check_single_instance():
        # 已有实例运行，直接退出（静默，不弹浏览器）
        sys.exit(0)

    # 首次运行自动注册开机自启（仅 exe 模式，已注册则跳过）
    from windows_service import ensure_autostart
    ensure_autostart()

    # 配置日志
    from config import LOG_FILE, DATA_DIR
    os.makedirs(DATA_DIR, exist_ok=True)

    # 无窗口模式下 sys.stdout 已被替换为空流，只保留文件日志
    log_handlers = []
    if args.console:
        log_handlers.append(logging.StreamHandler(sys.stdout))
    try:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        log_handlers.append(file_handler)
    except Exception:
        pass

    logging.basicConfig(
        level=logging.INFO,
        handlers=log_handlers,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 导入并启动 FastAPI 应用
    from main import app
    from config import API_HOST, API_PORT
    import uvicorn

    logger = logging.getLogger("FluxaVision")
    logger.info("FluxaVision 客流统计系统启动中...")

    # Windows 非控制台模式：启动托盘图标（后台线程）
    if sys.platform == "win32" and not args.console:
        from windows_service import setup_windows_tray
        try:
            import pystray
            from PIL import Image  # noqa: F401
            tray_thread = threading.Thread(
                target=setup_windows_tray, args=(API_PORT,), daemon=True
            )
            tray_thread.start()
        except ImportError:
            pass

    # 启动 Uvicorn（静默，不弹浏览器）
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    main()