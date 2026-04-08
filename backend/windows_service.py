"""
FluxaVision 客流统计系统 - Windows 服务封装

功能：
  1. 静默后台运行（无控制台窗口）
  2. 系统托盘图标（右键菜单：打开网页、重启服务、退出）
  3. 开机自启动（首次运行自动写入注册表，无需手动 --install）
  4. 单实例检查（防止重复启动）

运行方式：
  - 双击 FluxaVision.exe → 启动服务 + 托盘图标（静默，不弹浏览器）
  - FluxaVision.exe --uninstall → 卸载开机自启
  - FluxaVision.exe --console  → 控制台模式（调试用）
"""
import sys
import os
import threading
import time
import webbrowser

IS_WINDOWS = sys.platform == "win32"
IS_FROZEN = getattr(sys, 'frozen', False)


def _get_icon_path() -> str:
    """
    获取 logo.png 的运行时路径（用于桌面快捷方式图标）。
    注意：Windows 快捷方式图标需要 .ico 格式，所以这里返回 .ico 文件路径。
    """
    if IS_FROZEN:
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            p = os.path.join(meipass, 'assets', 'icon.ico')
            if os.path.isfile(p):
                return p
        p = os.path.join(os.path.dirname(sys.executable), 'assets', 'icon.ico')
        if os.path.isfile(p):
            return p
    else:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'icon.ico')
        if os.path.isfile(p):
            return p
    return ""


def _get_desktop_path() -> str:
    """获取桌面路径（读注册表，支持自定义桌面位置）"""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
        )
        desktop, _ = winreg.QueryValueEx(key, "Desktop")
        winreg.CloseKey(key)
        return desktop
    except Exception:
        return os.path.join(os.path.expanduser("~"), "Desktop")


def setup_windows_tray(app_port: int):
    """设置 Windows 系统托盘图标"""
    try:
        try:
            import pystray
            from PIL import Image
            _create_tray_pystray(app_port)
            return
        except ImportError:
            pass
        _create_tray_simple(app_port)
    except Exception as e:
        print(f"[Tray] 托盘图标创建失败: {e}，服务继续运行")


def _get_tray_image():
    """
    加载托盘图标图片。
    优先从 assets/icon.ico 加载，失败则尝试 logo.png，最后代码绘制兜底。
    """
    from PIL import Image, ImageDraw

    icon_paths = []

    # 优先使用 .ico 文件
    if IS_FROZEN:
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            icon_paths.append(os.path.join(meipass, 'assets', 'icon.ico'))
        icon_paths.append(os.path.join(os.path.dirname(sys.executable), 'assets', 'icon.ico'))
    else:
        icon_paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'icon.ico'))

    # 尝试加载图标文件
    for icon_path in icon_paths:
        if os.path.isfile(icon_path):
            try:
                print(f"[Tray] 加载图标: {icon_path}")
                return Image.open(icon_path).convert('RGBA')
            except Exception as e:
                print(f"[Tray] 加载图标失败: {e}")

    # 兜底：代码绘制
    print("[Tray] 使用代码绘制图标")
    image = Image.new('RGBA', (64, 64), (0, 217, 255, 255))
    dc = ImageDraw.Draw(image)
    dc.rectangle([15, 10, 25, 54], fill=(10, 25, 47, 255))
    dc.rectangle([28, 10, 49, 20], fill=(10, 25, 47, 255))
    dc.rectangle([28, 26, 49, 36], fill=(10, 25, 47, 255))
    dc.rectangle([28, 42, 42, 54], fill=(10, 25, 47, 255))
    return image


def _create_tray_pystray(app_port: int):
    """使用 pystray 创建带菜单的托盘图标"""
    import pystray

    try:
        image = _get_tray_image()
        print(f"[Tray] 图像大小: {image.size}")
    except Exception as e:
        print(f"[Tray] 加载图像失败: {e}")
        raise

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

    print("[Tray] 创建托盘图标...")
    tray = pystray.Icon("FluxaVision", image, "FluxaVision 客流统计系统", menu)
    print("[Tray] 托盘图标创建成功，开始运行...")
    tray.run()


def _create_tray_simple(app_port: int):
    """托盘不可用时的回退"""
    print(f"[Tray] 系统托盘不可用，请访问 http://127.0.0.1:{app_port}")


def install_autostart():
    """安装开机自启动（Windows 注册表 HKCU Run）"""
    if not IS_WINDOWS:
        print("[AutoStart] 仅支持 Windows 系统")
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


def _create_desktop_shortcut(app_port: int, icon_path: str):
    """
    在桌面创建管理面板快捷方式，双击用默认浏览器打开网页。
    """
    desktop = _get_desktop_path()
    url = f"http://127.0.0.1:{app_port}"

    # 使用 .url 文件格式，Windows 原生支持，双击自动用浏览器打开
    web_url = os.path.join(desktop, "FluxaVision 管理面板.url")
    if not os.path.exists(web_url):
        try:
            url_content = f"""[InternetShortcut]
URL={url}
IconIndex=0
"""
            if icon_path:
                url_content += f'IconFile={icon_path}\n'
            with open(web_url, 'w', encoding='utf-8') as f:
                f.write(url_content)
            print("[Shortcut] ✓ 管理面板快捷方式已创建")
        except Exception as e:
            print(f"[Shortcut] ✗ 管理面板快捷方式创建失败: {e}")


def _run_powershell(ps_command: str, label: str):
    """
    执行 PowerShell 脚本创建快捷方式。
    将脚本写入临时 .ps1 文件（UTF-8 BOM），再用 -File 执行，
    避免中文路径直接拼入 -Command 参数时的编码问题。
    """
    import subprocess
    import tempfile
    tmp = None
    try:
        # 写 UTF-8 BOM，PowerShell 默认以此判断编码
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.ps1', delete=False, encoding='utf-8-sig'
        ) as f:
            f.write(ps_command)
            tmp = f.name

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile", "-NonInteractive",
                "-ExecutionPolicy", "Bypass",
                "-File", tmp,
            ],
            capture_output=True, timeout=15,
        )
        if result.returncode == 0:
            print(f"[Shortcut] ✓ {label}已创建")
        else:
            print(f"[Shortcut] ✗ {label}创建失败: {result.stderr.decode(errors='ignore')}")
    except Exception as e:
        print(f"[Shortcut] ✗ {label}创建失败: {e}")
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass


def _create_lnk(lnk_path: str, exe_path: str, icon_path: str):
    """创建 exe 启动的 .lnk 快捷方式"""
    icon_line = f'$s.IconLocation = "{icon_path}"' if icon_path else ""
    ps = (
        "$ws = New-Object -ComObject WScript.Shell\n"
        f'$s = $ws.CreateShortcut("{lnk_path}")\n'
        f'$s.TargetPath = "{exe_path}"\n'
        f'$s.WorkingDirectory = "{os.path.dirname(exe_path)}"\n'
        '$s.Description = "FluxaVision 客流统计系统"\n'
        + (f"{icon_line}\n" if icon_line else "")
        + "$s.Save()"
    )
    _run_powershell(ps, "服务启动快捷方式")


def ensure_autostart():
    """
    首次运行时自动注册开机自启 + 创建桌面快捷方式，已注册则跳过。
    仅在 exe（IS_FROZEN）模式下生效，开发模式不执行。
    """
    if not IS_WINDOWS or not IS_FROZEN:
        return

    from config import API_PORT
    exe_path = os.path.abspath(sys.executable)
    icon_path = _get_icon_path()

    # ── 开机自启（注册表） ──────────────────────────────────────────────────
    already_registered = False
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ | winreg.KEY_SET_VALUE,
        )
        try:
            current_val, _ = winreg.QueryValueEx(key, "FluxaVision")
            already_registered = (current_val == f'"{exe_path}"')
        except FileNotFoundError:
            pass
        if not already_registered:
            winreg.SetValueEx(key, "FluxaVision", 0, winreg.REG_SZ, f'"{exe_path}"')
            print("[AutoStart] ✓ 已自动注册开机自启动")
        winreg.CloseKey(key)
    except Exception as e:
        print(f"[AutoStart] ✗ 自动注册失败: {e}")

    # ── 桌面快捷方式（每次都检查，支持用户删除后自动补回）─────────────────
    _create_desktop_shortcut(API_PORT, icon_path)


def uninstall_autostart():
    """卸载开机自启动"""
    if not IS_WINDOWS:
        print("[AutoStart] 仅支持 Windows 系统")
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
    """检查单实例运行（Windows 命名互斥体）"""
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