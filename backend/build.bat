@echo off
chcp 65001 >nul 2>&1
title FluxaVision 客流统计系统 - 构建工具

echo ══════════════════════════════════════════════════
echo    FluxaVision 客流统计系统 - 一键构建脚本
echo    Python后端 + Next.js前端 → exe安装包
echo ══════════════════════════════════════════════════
echo.

:: ==================== 环境检查 ====================
echo [1/6] 检查构建环境...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ 未找到 Node.js，请先安装 Node.js 18+
    pause
    exit /b 1
)

where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ 未找到 npm
    pause
    exit /b 1
)

echo ✓ Python 和 Node.js 环境检查通过

:: ==================== 安装依赖 ====================
echo.
echo [2/6] 安装 Python 依赖...
cd /d "%~dp0"
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ requirements.txt 依赖安装失败
    pause
    exit /b 1
)
pip install pyinstaller pystray Pillow >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ 打包工具安装失败
    pause
    exit /b 1
)
echo ✓ Python 依赖安装完成

echo.
echo [3/6] 安装 Node.js 依赖...
cd /d "%~dp0\.."
if not exist node_modules (
    call npm install
    if %errorlevel% neq 0 (
        echo ✗ Node.js 依赖安装失败
        pause
        exit /b 1
    )
)
echo ✓ Node.js 依赖已就绪

:: ==================== 构建前端 ====================
echo.
echo [4/6] 构建 Next.js 前端...
cd /d "%~dp0"

:: 备份原始 next.config.ts
if exist "..\next.config.ts" (
    copy "..\next.config.ts" "..\next.config.ts.bak" >nul 2>&1
)

:: 写入构建配置
(
echo import type { NextConfig } from "next";
echo const nextConfig: NextConfig = {
echo   output: "export",
echo   typescript: { ignoreBuildErrors: true },
echo   reactStrictMode: false,
echo   images: { unoptimized: true },
echo };
echo export default nextConfig;
) > "..\next.config.ts"

:: 构建
cd /d "%~dp0\.."
call npx next build
if %errorlevel% neq 0 (
    echo ✗ Next.js 构建失败
    if exist "..\next.config.ts.bak" (
        copy "..\next.config.ts.bak" "..\next.config.ts" >nul 2>&1
        del "..\next.config.ts.bak" >nul 2>&1
    )
    pause
    exit /b 1
)

:: 恢复原始配置
if exist "..\next.config.ts.bak" (
    copy "..\next.config.ts.bak" "..\next.config.ts" >nul 2>&1
    del "..\next.config.ts.bak" >nul 2>&1
)

:: 复制构建输出
cd /d "%~dp0"
if exist frontend-build rmdir /s /q frontend-build
xcopy "..\out" "frontend-build\" /E /I /Q >nul 2>&1
echo ✓ 前端构建完成

:: ==================== 检查图标 ====================
echo.
echo [5/6] 检查应用图标...
if exist "assets\icon.ico" (
    echo ✓ 使用已有图标: assets\icon.ico
) else (
    echo ✗ 未找到 assets\icon.ico，请先将图标文件放入 assets\ 目录
    pause
    exit /b 1
)

:: ==================== PyInstaller 打包 ====================
echo.
echo [6/6] PyInstaller 打包...
cd /d "%~dp0"
rmdir /s /q dist 2>nul
python -m PyInstaller --clean --noconfirm FluxaVision.spec
if %errorlevel% neq 0 (
    echo ✗ PyInstaller 打包失败
    pause
    exit /b 1
)
echo ✓ PyInstaller 打包完成

:: ==================== Inno Setup 安装程序 ====================
echo.
echo [可选] 构建 Inno Setup 安装程序...
where iscc >nul 2>&1
if %errorlevel% equ 0 (
    iscc installer.iss
    if %errorlevel% equ 0 (
        echo ✓ 安装程序构建完成
    )
) else (
    echo ⚠ 未找到 Inno Setup Compiler，跳过安装程序构建
    echo   下载地址: https://jrsoftware.org/isinfo.php
    echo   也可以直接使用 dist\FluxaVision\ 目录分发给用户
)

:: ==================== 构建摘要 ====================
echo.
echo ══════════════════════════════════════════════════
echo   构建完成！
echo ══════════════════════════════════════════════════
echo.
echo 输出目录: %~dp0dist\FluxaVision\
echo.
if exist "dist\FluxaVision\FluxaVision.exe" (
    echo 主程序: dist\FluxaVision\FluxaVision.exe
    for %%A in ("dist\FluxaVision\FluxaVision.exe") do echo 大小: %%~zA 字节
)
echo.
echo 运行方式:
echo   直接运行: FluxaVision.exe
echo   控制台调试: FluxaVision.exe --console
echo   指定端口: FluxaVision.exe --port 9000
echo   安装自启: FluxaVision.exe --install
echo   卸载自启: FluxaVision.exe --uninstall
echo.

pause