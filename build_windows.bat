@echo off
chcp 65001 >nul
title WorkMonitor 一键打包工具
color 0A

echo ====================================================
echo           WorkMonitor 一键打包工具
echo ====================================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 检查 Python 环境...
python --version
echo.

echo [2/4] 安装/更新依赖包...
pip install -q PyQt5 pynput pyinstaller
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo 依赖安装完成
echo.

echo [3/4] 清理旧文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist WorkMonitor.spec del /q WorkMonitor.spec
echo 清理完成
echo.

echo [4/4] 开始打包 WorkMonitor.exe...
echo 这可能需要几分钟，请耐心等待...
echo.

pyinstaller --name=WorkMonitor ^
            --onefile ^
            --windowed ^
            --clean ^
            --hidden-import=PyQt5 ^
            --hidden-import=PyQt5.QtCore ^
            --hidden-import=PyQt5.QtGui ^
            --hidden-import=PyQt5.QtWidgets ^
            --hidden-import=pynput.keyboard._win32 ^
            --hidden-import=pynput.mouse._win32 ^
            work_monitor.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo.
echo ====================================================
echo               打包成功！
echo ====================================================
echo.
echo 可执行文件位置: %cd%\dist\WorkMonitor.exe
echo.
echo 下一步:
echo 1. 运行 dist\WorkMonitor.exe 测试程序
echo 2. 右键托盘图标 -^> 设置 -^> 勾选"开机自动启动"
echo 3. 将 WorkMonitor.exe 复制到你想要的位置
echo.
echo ====================================================

REM 询问是否打开 dist 文件夹
echo.
set /p open="是否打开 dist 文件夹？(Y/N): "
if /i "%open%"=="Y" (
    explorer dist
)

pause