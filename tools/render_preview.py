"""离屏渲染预览工具：把若干关键画面导出为 PNG，便于核对还原度。

    python tools/render_preview.py [-o 输出目录]

不弹窗，使用 SDL dummy 驱动；输出 2x 高清图（1200x300）。
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import tempfile

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
# 预览不污染真实存档
os.environ['DINO_SCORE_FILE'] = os.path.join(tempfile.gettempdir(),
                                             'dino_preview_highscore.json')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

from dino.game import DinoGame  # noqa: E402

DT = 1000.0 / 60


class Sim:
    """用虚拟时钟驱动游戏，保证截图可复现。"""

    def __init__(self) -> None:
        self.game = DinoGame(muted=True, headless=True)
        self.t = 0

    def step(self, frames: int = 1) -> None:
        for _ in range(frames):
            self.t += DT
            self.game._now = int(self.t)
            self.game.update(DT, int(self.t))
            self.game.draw()

    def key_down(self, key: int) -> None:
        self.game._now = int(self.t)
        self.game.on_key_down(key)

    def key_up(self, key: int) -> None:
        self.game._now = int(self.t)
        self.game.on_key_up(key)

    def autopilot(self) -> None:
        """简单 AI：按障碍物宽度推算安全起跳窗口，中空翼龙则下蹲。"""
        game = self.game
        trex = game.trex
        if game.crashed:
            return
        obstacles = game.horizon.obstacles
        if not obstacles:
            if trex.ducking:
                self.key_up(pygame.K_DOWN)
            return

        first = obstacles[0]
        dist = first.x_pos - (trex.x_pos + trex.config['width'])
        kind = first.type_config['type']

        if kind == 'PTERODACTYL' and first.y_pos != 100:
            # 中/高空翼龙：蹲下通过（高空本就掠过，蹲着无害）
            if -first.width < dist < 220:
                if not trex.ducking:
                    self.key_down(pygame.K_DOWN)
                return
            if trex.ducking:
                self.key_up(pygame.K_DOWN)
            return

        if trex.ducking:
            self.key_up(pygame.K_DOWN)

        # 跳跃全程约 230px：越宽的障碍物必须越晚起跳
        if kind == 'CACTUS_LARGE':
            window = 70
        elif kind == 'CACTUS_SMALL':
            window = 95
        else:
            window = 90

        if not trex.jumping and 40 < dist < window:
            self.key_down(pygame.K_SPACE)
            self.key_up(pygame.K_SPACE)

    def shot(self, path: str) -> None:
        pygame.image.save(self.game.window, path)
        print(f'  saved {os.path.relpath(path, ROOT)}'
              f'  ({self.t / 1000:.2f}s,'
              f' score={self.game.distance_meter.get_actual_distance(self.game.distance_ran)})')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--out', default=os.path.join(ROOT, 'preview'))
    parser.add_argument('--seed', type=int, default=2024,
                        help='随机种子（决定障碍物布局，保证截图可复现）')
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    random.seed(args.seed)

    sim = Sim()
    sim.step(2)
    sim.shot(os.path.join(args.out, '01-idle.png'))

    # 第一次跳跃 -> 落地后开场动画 -> 世界开始滚动
    sim.key_down(pygame.K_SPACE)
    sim.step(6)
    sim.shot(os.path.join(args.out, '02-jump.png'))
    sim.key_up(pygame.K_SPACE)
    sim.step(70)
    sim.shot(os.path.join(args.out, '03-intro.png'))

    # 自动躲避跑 4 秒
    for _ in range(240):
        sim.autopilot()
        sim.step(1)
    sim.shot(os.path.join(args.out, '04-running.png'))

    # 下蹲（先清掉当前障碍物，避免截图中途撞车）
    sim.game.horizon.obstacles.clear()
    sim.step(2)
    sim.key_down(pygame.K_DOWN)
    sim.step(16)
    sim.shot(os.path.join(args.out, '05-ducking.png'))
    sim.key_up(pygame.K_DOWN)
    sim.step(4)

    # 切换夜间模式：等 CSS 1.5s 过渡走完再取景（期间清空障碍物，保持奔跑画面）
    sim.game.horizon.obstacles.clear()
    sim.game.invert_trigger = True
    sim.game.invert(False)
    for _ in range(96):
        sim.game.horizon.obstacles.clear()
        sim.step(1)
    sim.shot(os.path.join(args.out, '06-night.png'))

    # 关闭自动驾驶，等待撞上障碍物 -> Game Over
    sim.game.invert_trigger = False
    sim.game.invert(True)
    for _ in range(1800):
        sim.step(1)
        if sim.game.crashed:
            break
    if sim.game.crashed:
        # 等待重启按钮动画完整播完（875ms 静置 + 875ms 旋转）
        sim.step(2200)
        sim.shot(os.path.join(args.out, '07-gameover.png'))
    else:
        print('  ! 未触发游戏结束，跳过 07')

    pygame.quit()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
