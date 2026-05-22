"""
FluxaVision 客流统计系统 - PyInstaller 后处理脚本

在 Linux 容器中，可能遇到 "cannot enable executable stack" 错误，
这是内核安全限制导致的，在真实 Windows/Linux 系统上不会出现。

此脚本自动修复该问题（如果可以的话）。
"""
import os
import sys
import struct
import subprocess
import shutil

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "FluxaVision")
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def patch_elf_execstack(lib_path: str) -> bool:
    """直接修改 ELF 文件中的 GNU_STACK 段标志"""
    try:
        with open(lib_path, "rb") as f:
            data = bytearray(f.read())

        # ELF64 header
        if data[:4] != b'\x7fELF':
            return False

        # 读取 program header offset
        e_phoff = struct.unpack_from('<Q', data, 32)[0]
        e_phentsize = struct.unpack_from('<H', data, 54)[0]
        e_phnum = struct.unpack_from('<H', data, 56)[0]

        patched = False
        for i in range(e_phnum):
            offset = e_phoff + i * e_phentsize
            p_type = struct.unpack_from('<I', data, offset)[0]
            if p_type == 0x6474e551:  # PT_GNU_STACK
                old_flags = struct.unpack_from('<I', data, offset + 4)[0]
                if old_flags & 4:  # PF_X bit set
                    new_flags = old_flags & ~4  # Clear PF_X
                    struct.pack_into('<I', data, offset + 4, new_flags)
                    patched = True
                    print(f"  Patched {os.path.basename(lib_path)}: GNU_STACK {old_flags:#x} -> {new_flags:#x}")

        if patched:
            with open(lib_path, "wb") as f:
                f.write(data)
            return True
        return False
    except Exception as e:
        print(f"  Patch failed: {e}")
        return False


def patch_all_libraries():
    """尝试修复所有共享库的 execstack 问题"""
    internal_dir = os.path.join(DIST_DIR, "_internal")
    if not os.path.isdir(internal_dir):
        print(f"未找到 _internal 目录: {internal_dir}")
        return False

    # 方法1: 使用 execstack 工具
    try:
        result = subprocess.run(
            ["execstack", "-c"] + [
                os.path.join(internal_dir, f)
                for f in os.listdir(internal_dir)
                if f.endswith('.so') or f.endswith('.so.1.0')
            ],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            print("✓ execstack 修复完成")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 方法2: 使用 patchelf 工具
    try:
        result = subprocess.run(
            ["patchelf", "--clear-execstack", os.path.join(internal_dir, "libpython3.12.so.1.0")],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            print("✓ patchelf 修复完成")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 方法3: 直接修改 ELF 文件
    print("尝试直接修改 ELF 文件...")
    success = False
    for f in os.listdir(internal_dir):
        if '.so' in f:
            lib_path = os.path.join(internal_dir, f)
            if patch_elf_execstack(lib_path):
                success = True

    if success:
        print("✓ ELF 直接修改完成")
    else:
        print("⚠ 无法修复 execstack 问题")
        print("  这通常只在 Docker/容器环境中出现")
        print("  在真实的 Windows/Linux 系统上不会遇到此问题")
        print("  请在 Windows 上执行 build.bat 进行打包")

    return success


def main():
    print("=" * 50)
    print("  FluxaVision - 打包后处理")
    print("=" * 50)

    if not os.path.isdir(DIST_DIR):
        print(f"未找到打包输出: {DIST_DIR}")
        print("请先运行 PyInstaller 打包")
        sys.exit(1)

    patch_all_libraries()

    # 复制 VERSION 文件到 exe 同级目录（供 version.py 运行时读取）
    version_src = os.path.join(PROJECT_DIR, "VERSION")
    version_dst = os.path.join(DIST_DIR, "VERSION")
    if os.path.exists(version_src):
        shutil.copy2(version_src, version_dst)
        print(f" VERSION 文件已复制到: {version_dst}")

    # 打印输出大小
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(DIST_DIR):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)

    print(f"\n打包输出: {DIST_DIR}")
    print(f"总大小: {total_size / (1024*1024):.1f} MB")


if __name__ == "__main__":
    main()
