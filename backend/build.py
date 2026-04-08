"""
FluxaVision 客流统计系统 - 一键构建脚本 (Linux/macOS)

构建流程:
  1. 构建 Vue 3 + Vite 前端静态文件
  2. 将静态文件复制到 backend/frontend-build/
  3. 使用 PyInstaller 打包 Python 后端 + 前端 → dist/FluxaVision/

使用方法:
  cd backend
  python build.py

前置条件:
  - Node.js >= 18
  - Python >= 3.10
  - pip install pyinstaller
"""
import os
import sys
import shutil
import subprocess

# ==================== 路径配置 ====================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
FRONTEND_BUILD_DIR = os.path.join(SCRIPT_DIR, "frontend-build")
FRONTEND_VUE_DIR = os.path.join(PROJECT_DIR, "frontend-vue")


def run_cmd(cmd: str, cwd: str, description: str) -> bool:
    """运行命令并打印进度"""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"  命令: {cmd}")
    print(f"  目录: {cwd}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"✗ {description} 失败 (exit code: {result.returncode})")
        return False
    print(f"✓ {description} 成功")
    return True


def build_frontend():
    """步骤1: 构建 Vue 3 + Vite 前端静态文件"""
    print(f"\n[1/4] 构建 Vue 前端静态文件...")

    # 安装依赖（如果需要）
    if not os.path.exists(os.path.join(FRONTEND_VUE_DIR, "node_modules")):
        if not run_cmd("npm install", FRONTEND_VUE_DIR, "安装 Vue 前端依赖"):
            return False

    # 构建 Vue
    if not run_cmd("npm run build", FRONTEND_VUE_DIR, "Vite 构建"):
        return False

    # 检查输出
    dist_dir = os.path.join(FRONTEND_VUE_DIR, "dist")
    if not os.path.isdir(dist_dir):
        print(f"✗ 未找到构建输出目录: {dist_dir}")
        return False

    # 复制到 frontend-build
    if os.path.exists(FRONTEND_BUILD_DIR):
        shutil.rmtree(FRONTEND_BUILD_DIR)
    shutil.copytree(dist_dir, FRONTEND_BUILD_DIR)

    print(f"✓ 前端静态文件已复制到: {FRONTEND_BUILD_DIR}")
    return True


def build_pyinstaller():
    """步骤2: 使用 PyInstaller 打包"""
    print(f"\n[2/4] PyInstaller 打包后端...")

    spec_file = os.path.join(SCRIPT_DIR, "FluxaVision.spec")
    dist_dir = os.path.join(SCRIPT_DIR, "dist")

    # 清理旧输出
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)

    # 运行 PyInstaller
    if not run_cmd(
        f'"{sys.executable}" -m PyInstaller --clean --noconfirm "{spec_file}"',
        SCRIPT_DIR,
        "PyInstaller 打包"
    ):
        return False

    # 验证输出
    exe_dir = os.path.join(dist_dir, "FluxaVision")
    if not os.path.isdir(exe_dir):
        print(f"✗ 未找到打包输出: {exe_dir}")
        return False

    print(f"✓ 打包完成: {exe_dir}")

    # 后处理：修复 Linux execstack 问题
    try:
        print("\n[后处理] 修复共享库兼容性...")
        sys.path.insert(0, SCRIPT_DIR)
        from post_build import patch_all_libraries
        patch_all_libraries()
    except Exception as e:
        print(f"⚠ 后处理跳过: {e}")

    return True


def build_installer():
    """步骤3: 构建 Windows 安装程序 (如果在Windows上)"""
    if sys.platform != "win32":
        print(f"\n[3/4] 跳过 Windows 安装程序构建（非Windows系统）")
        return True

    print(f"\n[3/4] 构建 Inno Setup 安装程序...")

    iscc_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if not os.path.exists(iscc_path):
        iscc_path = r"C:\Program Files\Inno Setup 6\ISCC.exe"

    if not os.path.exists(iscc_path):
        print(f"✗ 未找到 Inno Setup Compiler: {iscc_path}")
        print(f"  请下载安装: https://jrsoftware.org/isinfo.php")
        return False

    iss_file = os.path.join(SCRIPT_DIR, "installer.iss")
    if not run_cmd(f'"{iscc_path}" "{iss_file}"', SCRIPT_DIR, "Inno Setup 编译"):
        return False

    return True


def generate_icon():
    """步骤0: 生成应用图标"""
    print(f"\n[0/4] 生成应用图标...")
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from create_icon import create_icon
        assets_dir = os.path.join(SCRIPT_DIR, "assets")
        os.makedirs(assets_dir, exist_ok=True)
        icon_path = os.path.join(assets_dir, "icon.ico")
        create_icon(icon_path)
    except Exception as e:
        print(f"⚠ 图标生成跳过: {e}（不影响打包）")


def print_summary():
    """打印构建摘要"""
    print(f"\n{'='*60}")
    print(f"  构建完成！")
    print(f"{'='*60}")
    exe_dir = os.path.join(SCRIPT_DIR, "dist", "FluxaVision")
    print(f"  输出目录: {exe_dir}")
    print(f"{'='*60}")

    if sys.platform == "win32":
        exe_path = os.path.join(exe_dir, "FluxaVision.exe")
    else:
        exe_path = os.path.join(exe_dir, "FluxaVision")

    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"  主程序: {exe_path}")
        print(f"  大小: {size_mb:.1f} MB")

    # 统计总大小
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(exe_dir):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    print(f"  总大小: {total_size / (1024 * 1024):.1f} MB")
    print(f"{'='*60}")
    print(f"\n运行方式:")
    print(f"  直接运行: {exe_path}")
    print(f"  控制台模式: {exe_path} --console")
    print(f"  指定端口: {exe_path} --port 9000")
    print(f"  安装自启: {exe_path} --install")
    print(f"  卸载自启: {exe_path} --uninstall")
    print(f"")


def main():
    print(f"""
╔══════════════════════════════════════════════════╗
║       FluxaVision 客流统计系统 - 构建工具         ║
║       Python后端 + Next.js前端 → exe安装包        ║
╚══════════════════════════════════════════════════╝
    """)

    # 步骤0: 生成图标
    generate_icon()

    # 步骤1: 构建前端
    if not build_frontend():
        print("\n✗ 前端构建失败，构建中止")
        sys.exit(1)

    # 步骤2: PyInstaller 打包
    if not build_pyinstaller():
        print("\n✗ PyInstaller 打包失败，构建中止")
        sys.exit(1)

    # 步骤3: Inno Setup 安装程序（可选）
    build_installer()

    # 打印摘要
    print_summary()


if __name__ == "__main__":
    main()
