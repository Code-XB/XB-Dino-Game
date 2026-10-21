"""云朵 —— 1:1 移植自官方 cloud.ts。"""

from __future__ import annotations

import math
import random

from .. import settings
from ..assets import Renderer


class Cloud:
    def __init__(self, renderer: Renderer, container_width: int) -> None:
        self.renderer = renderer
        self.x_pos = float(container_width)
        self.remove = False
        self.gap = random.randint(settings.CLOUD['min_cloud_gap'],
                                  settings.CLOUD['max_cloud_gap'])
        self.y_pos = random.randint(settings.CLOUD['max_sky_level'],
                                    settings.CLOUD['min_sky_level'])

    def update(self, speed: float) -> None:
        if not self.remove:
            self.x_pos -= math.ceil(speed)
            if not self.is_visible():
                self.remove = True

    def is_visible(self) -> bool:
        return self.x_pos + settings.CLOUD['width'] > 0

    def draw(self) -> None:
        self.renderer.draw('cloud', self.x_pos, self.y_pos)
