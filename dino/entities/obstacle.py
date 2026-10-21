"""障碍物（仙人掌 / 翼龙）—— 1:1 移植自官方 obstacle.ts。"""

from __future__ import annotations

import math
import random

from .. import settings
from ..assets import Renderer

# obstacle.ts 模块级常量
max_gap_coefficient = settings.MAX_GAP_COEFFICIENT
max_obstacle_length = settings.RUNNER['max_obstacle_length']


class Obstacle:
    def __init__(self, renderer: Renderer, type_config: dict,
                 dimensions_width: int, gap_coefficient: float,
                 speed: float, x_offset: float = 0) -> None:
        self.renderer = renderer
        self.type_config = type_config
        self.gap_coefficient = gap_coefficient
        self.size = random.randint(1, max_obstacle_length)
        self.x_pos = dimensions_width + x_offset
        self.remove = False
        self.following_obstacle_created = False
        self.current_frame = 0
        self.timer = 0.0
        self.speed_offset = 0.0
        self.collision_boxes: list[tuple[int, int, int, int]] = []
        self.gap = 0.0
        self.y_pos = 0.0
        self.width = 0.0

        self._init(speed)

    # ------------------------------------------------------------------
    def _init(self, speed: float) -> None:
        self._clone_collision_boxes()

        # 速度不足时不生成多株
        if self.size > 1 and self.type_config['multiple_speed'] > speed:
            self.size = 1

        self.width = self.type_config['width'] * self.size

        # 翼龙有多种飞行高度
        y_pos = self.type_config['y_pos']
        if isinstance(y_pos, list):
            self.y_pos = y_pos[random.randint(0, len(y_pos) - 1)]
        else:
            self.y_pos = y_pos

        # 多株时的碰撞盒调整：中间盒加宽、末盒右移
        # (官方注释见 obstacle.ts init())
        if self.size > 1:
            self.collision_boxes[1] = (
                self.collision_boxes[1][0],
                self.collision_boxes[1][1],
                round(self.width - self.collision_boxes[0][2]
                      - self.collision_boxes[2][2]),
                self.collision_boxes[1][3])
            self.collision_boxes[2] = (
                round(self.width - self.collision_boxes[2][2]),
                self.collision_boxes[2][1],
                self.collision_boxes[2][2],
                self.collision_boxes[2][3])

        # 翼龙与地面速度略有差异
        if self.type_config.get('speed_offset'):
            sign = 1 if random.random() > 0.5 else -1
            self.speed_offset = sign * self.type_config['speed_offset']

        self.gap = self._get_gap(self.gap_coefficient, speed)

    def _clone_collision_boxes(self) -> None:
        self.collision_boxes = [tuple(box)
                                for box in self.type_config['collision_boxes']]

    def _get_gap(self, gap_coefficient: float, speed: float) -> float:
        min_gap = round(self.width * speed
                        + self.type_config['min_gap'] * gap_coefficient)
        max_gap = round(min_gap * max_gap_coefficient)
        return random.randint(min_gap, max_gap)

    # ------------------------------------------------------------------
    def update(self, delta_time: float, speed: float) -> None:
        if self.remove:
            return
        if self.type_config.get('speed_offset'):
            speed += self.speed_offset
        self.x_pos -= math.floor(speed * settings.FPS / 1000 * delta_time)

        # 帧动画（翼龙扇翅）
        if self.type_config.get('num_frames'):
            self.timer += delta_time
            if self.timer >= self.type_config['frame_rate']:
                self.current_frame = (0 if self.current_frame ==
                                      self.type_config['num_frames'] - 1
                                      else self.current_frame + 1)
                self.timer = 0

        if not self.is_visible():
            self.remove = True

    def is_visible(self) -> bool:
        return self.x_pos + self.width > 0

    def draw(self) -> None:
        cfg = self.type_config
        name = ('pterodactyl' if cfg['type'] == 'PTERODACTYL'
                else 'cactus_small' if cfg['type'] == 'CACTUS_SMALL'
                else 'cactus_large')
        # 帧号：仙人掌按株数取帧，翼龙按动画帧取帧
        frame = (self.current_frame if cfg['type'] == 'PTERODACTYL'
                 else self.size - 1)
        self.renderer.draw(name, self.x_pos, self.y_pos, frame=frame)
