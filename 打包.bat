@echo off
rem ============================================================
rem  XB-Dino-Game 一键打包：Nuitka 单文件 exe + Inno Setup 安装包
rem  产物：build\XB-Dino-Game.exe / installer\XB-Dino-Game-Setup-*.exe
rem  依赖：python(含 pygame) + nuitka + zstandard + Inno Setup 6
rem ============================================================
setlocal
title XB-Dino-Game Build
cd /d "%~dp0"

set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"

echo.
echo  [1/2] Nuitka 打包单文件 exe（首次较慢，需下载编译器）...
python -m nuitka --standalone --onefile ^
  --windows-icon-from-ico=icon.ico ^
  --windows-console-mode=disable ^
  --include-data-files=icon.ico=icon.ico ^
  --include-data-dir=assets=assets ^
  --windows-company-name=Code-XB ^
  --windows-product-name=XB-Dino-Game ^
  --windows-file-version=1.0.0 ^
  --windows-product-version=1.0.0 ^
  --windows-file-description="Google Chrome T-Rex Runner (Python Remake)" ^
  --output-dir=build --output-filename=XB-Dino-Game.exe ^
  --assume-yes-for-downloads --lto=no main.py
if errorlevel 1 (
    echo  [错误] Nuitka 打包失败！
    pause & exit /b 1
)

echo.
echo  [2/2] Inno Setup 编译安装包...
%ISCC% setup.iss
if errorlevel 1 (
    echo  [错误] 安装包编译失败！
    pause & exit /b 1
)

echo.
echo  ============================================
echo   完成！
echo    便携版: build\XB-Dino-Game.exe
echo    安装版: installer\XB-Dino-Game-Setup-1.0.0.exe
echo  ============================================
pause
