# XB-Dino-Game v1.0.0 发布说明

> Google Chrome 小恐龙（T-Rex Runner）的 Python 1:1 复刻版
> 素材与音效均来自 Chromium 官方仓库，逻辑逐行对照官方源码移植。

##  特性

- **1:1 官方还原**：精灵图、音效全部来自 Chromium 官方；跳跃物理、碰撞盒、
  速度曲线（6→13）与网页版完全一致
- **完整游戏机制**：
  - 按住空格连跳、按住跳更高、空中按下快速落地
  - 下蹲躲避翼龙（三种飞行高度）、仙人掌 1~3 株连排
  - 待机随机眨眼、44px→600px 开场展开动画
- **昼夜系统**：每 700 分入夜（1.5s 贝塞尔曲线过渡）、持续 12s，
  月相七变化 + 星星视差
- **计分系统**：每 100 分闪烁 + 音效、最高分本地持久化
- **Game Over 动画**：Chrome logo → 重启按钮旋转过渡，与原版一致
- **桌面应用级体验**：安装版支持窗口/任务栏/标题栏统一图标、
  失焦自动暂停、回窗自动继续

## 操作

| 按键 | 功能 |
| --- | --- |
| 空格 / ↑ / W | 起跳（按住 = 连跳 + 跳得更高） |
| ↓ / S | 下蹲；空中按下 = 快速落地 |
| Enter / 空格 | 游戏结束后重开 |
| P | 暂停 / 继续 |
| M | 静音 |
| Esc | 退出 |

## 安装

- **安装版**（推荐）：下载 `XB-Dino-Game-Setup-1.0.0.exe`，
  双击安装，和正经应用一样——开始菜单/桌面快捷方式、控制面板可卸载
- **便携版**：下载 `XB-Dino-Game-1.0.0-portable.exe`，单文件直接运行，
  无需安装、无需 Python 环境

## 说明

- 最高分保存在 `%APPDATA%\XB-Dino-Game\highscore.json`（安装版）
  或程序同目录（便携版/源码运行）
- 系统要求：Windows 10/11 x64
- 开源地址：<https://github.com/Code-XB/XB-Dino-Game>

## 致谢

- [Chromium](https://github.com/chromium/chromium) — 官方游戏源码与素材
- [pygame-ce](https://pyga.me/) — 游戏运行时
- [Nuitka](https://nuitka.net/) / [Inno Setup](https://jrsoftware.org/isinfo.php) — 打包与安装程序
