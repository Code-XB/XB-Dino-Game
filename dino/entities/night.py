"""夜间模式（月亮 + 星星）—— 1:1 移植自官方 night_mode.ts。"""

from __future__ import annotations

import random

from .. import settings
from ..assets import Renderer

PHASES = settings.MOON_PHASES


class NightMode:
    def __init__(self, renderer: Renderer, container_width: int) -> None:
        self.renderer = renderer
        # 注意：官方 Horizon 构造时传入的是容器高度（150），此处保持一致
        self.container_width = container_width
        self.x_pos = 0.0
        self.y_pos = 30
        self.current_phase = 0
        self.opacity = 0.0
        self.draw_stars = False
        self.stars: list[dict] = []
        self._place_stars()

    def update(self, activated: bool) -> None:
        # 月相推进
        if activated and self.opacity == 0:
            self.current_phase += 1
            if self.current_phase >= len(PHASES):
                self.current_phase = 0

        # 淡入 / 淡出
        if activated and (self.opacity < 1 or self.opacity == 0):
            self.opacity += settings.NIGHT['fade_speed']
        elif self.opacity > 0:
            self.opacity -= settings.NIGHT['fade_speed']

        # 移动月亮与星星
        if self.opacity > 0:
            self.x_pos = self._update_x_pos(self.x_pos,
                                            settings.NIGHT['moon_speed'])
            if self.draw_stars:
                for star in self.stars:
                    star['x'] = self._update_x_pos(star['x'],
                                                   settings.NIGHT['star_speed'])
        else:
            self.opacity = 0
            self._place_stars()
        self.draw_stars = True

    def draw(self) -> None:
        if self.opacity <= 0:
            return
        phase = self.current_phase
        # 满月（第 4 相）源宽为 2 倍
        alpha = round(self.opacity * 255)

        if self.draw_stars:
            for i, star in enumerate(self.stars):
                self.renderer.draw('star', round(star['x']), star['y'],
                                   frame=i % 2, alpha=alpha)
        self.renderer.draw('moon', round(self.x_pos), self.y_pos,
                           frame=phase, alpha=alpha)

    def _update_x_pos(self, current_pos: float, speed: float) -> float:
        if current_pos < -settings.NIGHT['width']:
            current_pos = self.container_width
        else:
            current_pos -= speed
        return current_pos

    def _place_stars(self) -> None:
        segment = round(self.container_width / settings.NIGHT['num_stars'])
        self.stars = []
        for i in range(settings.NIGHT['num_stars']):
            self.stars.append({
                'x': random.randint(segment * i, segment * (i + 1)),
                'y': random.randint(0, settings.NIGHT['star_max_y']),
            })

    def reset(self) -> None:
        self.current_phase = 0
        self.opacity = 0
        self.update(False)
