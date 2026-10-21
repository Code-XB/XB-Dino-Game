@echo off
rem ============================================================
rem  Google 小恐龙 (XB-Dino-Game) 启动脚本
rem  功能：检查 Python 环境 -> 检查/安装 pygame -> 启动游戏
rem  注意：本文件必须以 ANSI(GBK) 编码 + CRLF 换行保存
rem ============================================================
setlocal
title Google XiaoKongLong - Python FuKeBan
cd /d "%~dp0"

echo.
echo  ============================================
echo    Google 小恐龙 (T-Rex Runner) Python 复刻版
echo  ============================================
echo.

rem ---- 1. 检查 Python ----
where python >nul 2>nul
if errorlevel 1 (
    echo  [错误] 未找到 Python，请先安装 Python 3.10 或更高版本，
    echo         安装时务必勾选 "Add Python to PATH"。
    echo         下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [OK] 已找到 Python %PYVER%

rem ---- 2. 检查 pygame ----
python -c "import pygame" >nul 2>nul
if errorlevel 1 (
    echo  [提示] 未检测到 pygame，正在自动安装...
    python -m pip install pygame
    if errorlevel 1 (
        echo  [错误] pygame 安装失败，请检查网络后重试，
        echo         或手动执行: python -m pip install pygame
        echo.
        pause
        exit /b 1
    )
    echo  [OK] pygame 安装完成
) else (
    for /f "tokens=*" %%p in ('python -c "import pygame;print(pygame.version.ver)" 2^>nul') do set PGVER=%%p
    echo  [OK] pygame 已安装
)

rem ---- 3. 启动游戏 ----
echo.
echo  正在启动游戏...（空格/上 跳跃，下 下蹲，Enter 重开，P 暂停，M 静音）
echo.
python main.py
if errorlevel 1 (
    echo.
    echo  [错误] 游戏异常退出，请把上方报错信息反馈给开发者。
    pause
)
endlocal
