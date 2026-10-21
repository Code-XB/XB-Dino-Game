"""程序入口。

用法：
    python main.py                # 1200x300（高清 2x 渲染，1:1 还原）
    python main.py --scale 2      # 放大到 2400x600
    python main.py --mute         # 静音启动

操作：
    空格 / ↑ / W   起跳（按住可跳得更高）
    ↓ / S          下蹲（空中按下 = 快速落地）
    Enter          游戏结束后立即重开
    鼠标点击        游戏结束后点击重开按钮
    P              暂停 / 继续      M  静音 / 取消静音      Esc  退出
"""

from __future__ import annotations

import argparse
import sys


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Google Chrome 小恐龙（T-Rex Runner）Python 复刻版')
    parser.add_argument('--scale', type=float, default=1.0,
                        help='窗口缩放倍数（默认 1.0，即 1200x300 像素）')
    parser.add_argument('--mute', action='store_true', help='静音启动')
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    import pygame  # 延迟导入，保证 --help 在无 pygame 环境也可见

    from dino.game import DinoGame

    try:
        game = DinoGame(scale=args.scale, muted=args.mute)
    except pygame.error as exc:      # 无显示设备 / 无声卡等
        print(f'初始化失败：{exc}', file=sys.stderr)
        return 1

    try:
        game.run()
    except KeyboardInterrupt:
        pygame.quit()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
