# T-Rex Runner · Google Chrome 小恐龙（Python 复刻版）

对 Chrome 断网页面的小恐龙游戏做 **1:1 复刻**：所有常量、动画帧、碰撞盒、
计分与昼夜切换逻辑均逐行对照 Chromium 官方源码
（`components/neterror/resources/dino_game/*.ts`）移植；美术资源直接使用
官方精灵图与三段原版音效。

## 运行

**Windows 一键启动**：双击 `启动.bat`（自动检查 Python 与 pygame，缺依赖会自动安装）。

或手动运行：

```bash
pip install -r requirements.txt
python main.py              # 1200x300（官方 2x 高清渲染）
python main.py --scale 2    # 放大一倍
python main.py --mute       # 静音启动
```

## 操作

| 按键 | 功能 |
| --- | --- |
| 空格 / ↑ / W | 起跳（提前松开 = 矮跳，跳得更高需按住）；**按住不放 = 落地后连续跳** |
| ↓ / S | 下蹲；空中按下 = 快速落地 |
| Enter | 游戏结束后立即重开 |
| 空格 / ↑ | 游戏结束 1.2s 后按可重开；暂停时按可继续 |
| 鼠标点击 | 点击 GAME OVER 中央按钮重开 |
| P | 暂停 / 继续 |
| 失去焦点 | 窗口切到后台自动暂停，回到窗口自动继续 |
| M | 静音 / 取消静音 |
| Esc | 退出 |

## 还原的行为细节

- 待机时恐龙随机眨眼（1~7s 间隔，最多 3 次），落位与"线穿脚踝"完全一致
- 第一次跳跃落地后播放开场动画：可视区域 44px → 600px（CSS `ease-out` 曲线）
- 速度初值 6、每帧 +0.001、上限 13；障碍物间距按 `width*speed + minGap*0.6` 随机
- 仙人掌 1~3 株连排，翼龙 8.5 速后出现、三种飞行高度、0.8 速度扰动
- 每 100 分闪烁 + 原版音效；分数超过 99999 扩展一位（与官方一致仅扩展一次）
- 每 700 分切换昼夜：`filter: invert(1)` 过渡曲线 `cubic-bezier(.65,.05,.36,1)`，
  夜间持续 12s；月亮七种月相、两颗星星、独立视差速度
- 碰撞盒逐像素采用官方数据（含多株仙人掌的加宽/偏移修正）
- Game Over 面板：重启按钮"静置 → 旋转一周 → 循环"动画
- 最高分持久化到 `highscore.json`（对应 Chrome Profile 存档）

## 项目结构

```
XB-Dino-Game/
├── main.py                    # 入口（命令行参数解析）
├── requirements.txt
├── assets/
│   ├── sprites/               # Chromium 官方精灵图（1x / 2x）
│   └── audio/                 # 官方音效：起跳、撞击、达成
├── dino/
│   ├── settings.py            # 全部常量（注释标明对应的官方 .ts 文件）
│   ├── assets.py              # 精灵图裁剪 / 夜间反色 / 日夜双画布合成
│   ├── audio.py               # 音效管理
│   ├── collision.py           # 碰撞检测（checkForCollision / boxCompare）
│   ├── storage.py             # 最高分持久化
│   ├── utils.py               # JS 语义工具（Math.round 等）
│   ├── game.py                # 主循环（对应官方 offline.ts Runner）
│   ├── entities/
│   │   ├── trex.py            # 恐龙（眨眼/跳跃/下蹲/死亡）
│   │   ├── obstacle.py        # 仙人掌与翼龙
│   │   ├── horizon.py         # 地面滚动 + 障碍物调度 + 云
│   │   ├── cloud.py           # 云朵
│   │   └── night.py           # 夜间模式（月亮/星星）
│   └── ui/
│       ├── distance_meter.py  # 计分器
│       └── game_over_panel.py # 结束面板
├── tools/
│   └── render_preview.py      # 离屏渲染关键画面到 preview/*.png
└── preview/                   # 预览截图（可删除后重新生成）
```

## 素材来源

- 精灵图：`chromium/chromium` 仓库 `components/neterror/resources/images/`
- 音效：同仓库 `components/neterror/resources/sounds/`
- 逻辑参考：同仓库 `components/neterror/resources/dino_game/*.ts`
