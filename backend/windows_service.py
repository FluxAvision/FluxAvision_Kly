"""
FluxaVision 客流统计系统 - Windows 服务封装

功能：
  1. 静默后台运行（无控制台窗口）
  2. 系统托盘图标（右键菜单：打开网页、重启服务、退出）
  3. 开机自启动（写入注册表）
  4. 单实例检查（防止重复启动）

运行方式：
  - 双击 FluxaVision.exe → 启动服务 + 托盘图标
  - FluxaVision.exe --install → 安装为开机自启
  - FluxaVision.exe --uninstall → 卸载开机自启
  - FluxaVision.exe --console → 控制台模式（调试用）
"""
import sys
import os
import threading
import time
import webbrowser

# 在导入 Windows 特定模块前，先检测平台
IS_WINDOWS = sys.platform == "win32"
IS_FROZEN = getattr(sys, 'frozen', False)


def setup_windows_tray(app_port: int):
    """设置 Windows 系统托盘图标"""
    try:
        import ctypes
        from ctypes import wintypes

        # 尝试使用 pystray 创建托盘图标
        try:
            import pystray
            from PIL import Image, ImageDraw
            _create_tray_pystray(app_port)
            return
        except ImportError:
            pass

        # 回退: 使用 ctypes 创建简单托盘（仅通知区域，无菜单）
        _create_tray_simple(app_port)

    except Exception as e:
        print(f"[Tray] 托盘图标创建失败: {e}，服务继续运行")


def _create_tray_pystray(app_port: int):
    """使用 pystray 创建带菜单的托盘图标"""
    import pystray
    from PIL import Image, ImageDraw

    # 创建一个简单的图标
    width, height = 64, 64
    image = Image.new('RGBA', (width, height), (0, 217, 255, 255))
    dc = ImageDraw.Draw(image)
    # 画一个 "F" 字母作为 Logo
    dc.rectangle([15, 10, 25, 54], fill=(10, 25, 47, 255))
    dc.rectangle([28, 10, 49, 20], fill=(10, 25, 47, 255))
    dc.rectangle([28, 26, 49, 36], fill=(10, 25, 47, 255))
    dc.rectangle([28, 42, 42, 54], fill=(10, 25, 47, 255))

    def open_web(icon, item):
        webbrowser.open(f"http://127.0.0.1:{app_port}")

    def restart(icon, item):
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def quit_app(icon, item):
        icon.stop()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("FluxaVision 客流统计", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("打开管理面板", open_web),
        pystray.MenuItem("重启服务", restart),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", quit_app),
    )

    tray = pystray.Icon("FluxaVision", image, "FluxaVision 客流统计系统", menu)
    tray.run()


def _create_tray_simple(app_port: int):
    """使用最简单的方式 - 仅打印信息"""
    print(f"[Tray] 系统托盘不可用，请访问 http://127.0.0.1:{app_port}")


def install_autostart():
    """安装开机自启动（Windows注册表）"""
    if not IS_WINDOWS:
        print("[AutoStart] 仅支持Windows系统")
        return False

    try:
        import winreg
        exe_path = os.path.abspath(sys.executable if IS_FROZEN else __file__)
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, "FluxaVision", 0, winreg.REG_SZ, f'"{exe_path}"')
        winreg.CloseKey(key)
        print("[AutoStart] ✓ 开机自启动已安装")
        return True
    except Exception as e:
        print(f"[AutoStart] ✗ 安装失败: {e}")
        return False


def uninstall_autostart():
    """卸载开机自启动"""
    if not IS_WINDOWS:
        print("[AutoStart] 仅支持Windows系统")
        return False

    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE,
        )
        winreg.DeleteValue(key, "FluxaVision")
        winreg.CloseKey(key)
        print("[AutoStart] ✓ 开机自启动已卸载")
        return True
    except FileNotFoundError:
        print("[AutoStart] 未找到自启动配置")
        return False
    except Exception as e:
        print(f"[AutoStart] ✗ 卸载失败: {e}")
        return False


def check_single_instance():
    """检查单实例运行（Windows命名互斥体）"""
    if not IS_WINDOWS:
        return True

    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        mutex_name = "Global\\FluxaVision_Traffic_Counter_SingleInstance"
        mutex = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()

        if last_error == 183:  # ERROR_ALREADY_EXISTS
            print("[Instance] FluxaVision 已在运行中")
            return False
        return True
    except Exception:
        return True


def auto_open_browser(port: int):
    """延迟打开浏览器"""
    def _open():
        time.sleep(2)
        try:
            webbrowser.open(f"http://127.0.0.1:{port}")
        except Exception:
            pass
    threading.Thread(target=_open, daemon=True).start()
