"""
FluxaVision 客流统计系统 - 入口启动器

这是 PyInstaller 打包的入口文件。
负责：解析命令行参数 → 初始化服务 → 启动后端 → 托盘图标
"""
import sys
import os

# 确保 backend 目录在 Python 路径中
if getattr(sys, 'frozen', False):
    # PyInstaller onedir: 添加 exe 所在目录
    sys.path.insert(0, os.path.dirname(sys.executable))
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
import argparse

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
        # 如果已有实例运行，尝试打开浏览器
        from config import API_PORT
        try:
            import webbrowser
            webbrowser.open(f"http://127.0.0.1:{API_PORT}")
        except Exception:
            pass
        sys.exit(0)

    # 配置日志
    from config import LOG_FILE, DATA_DIR
    os.makedirs(DATA_DIR, exist_ok=True)

    log_handlers = [logging.StreamHandler(sys.stdout)]
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

    # 非控制台模式下，自动打开浏览器
    if not args.console:
        from windows_service import auto_open_browser, setup_windows_tray
        auto_open_browser(API_PORT)

        # 在 Windows 非控制台模式下启动托盘（在子线程中）
        if sys.platform == "win32" and not args.console:
            tray_thread = None
            try:
                import pystray
                from PIL import Image  # noqa: F401
                tray_thread = threading.Thread(
                    target=setup_windows_tray, args=(API_PORT,), daemon=True
                )
                tray_thread.start()
            except ImportError:
                pass
    import threading

    # 启动 Uvicorn
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    main()
