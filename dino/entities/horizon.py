"""地平线（地面 + 云 + 障碍物 + 夜间模式）—— 移植自官方 horizon.ts / horizon_line.ts。"""

from __future__ import annotations

import random

from .. import settings
from ..assets import Renderer
from .cloud import Cloud
from .night import NightMode
from .obstacle import Obstacle


class HorizonLine:
    """由两段 600x12 的地面拼接而成，随机切换平地/凸起纹理。"""

    def __init__(self, renderer: Renderer) -> None:
        self.renderer = renderer
        cfg = settings.HORIZON_LINE
        self.width = cfg['width']
        self.height = cfg['height']
        self.y_pos = cfg['y_pos']
        self.source_x_pos = [cfg['source_x'], cfg['source_x'] + self.width]
        self.x_pos = [0.0, float(self.width)]
        self.bump_threshold = cfg['bump_threshold']

    def _get_random_type(self) -> int:
        return self.width if random.random() > self.bump_threshold else 0

    def _update_x_pos(self, pos: int, increment: int) -> None:
        line1 = pos
        line2 = 1 if pos == 0 else 0

        self.x_pos[line1] -= increment
        self.x_pos[line2] = self.x_pos[line1] + self.width

        if self.x_pos[line1] <= -self.width:
            self.x_pos[line1] += self.width * 2
            self.x_pos[line2] = self.x_pos[line1] - self.width
            self.source_x_pos[line1] = self._get_random_type() \
                + settings.HORIZON_LINE['source_x']

    def update(self, delta_time: float, speed: float) -> None:
        increment = int(speed * (settings.FPS / 1000) * delta_time)
        self._update_x_pos(0 if self.x_pos[0] <= 0 else 1, increment)

    def draw(self) -> None:
        base = settings.HORIZON_LINE['source_x']
        for i in (0, 1):
            name = 'horizon_0' if self.source_x_pos[i] == base else 'horizon_1'
            self.renderer.draw(name, self.x_pos[i], self.y_pos)

    def reset(self) -> None:
        self.x_pos[0] = 0
        self.x_pos[1] = self.width


class Horizon:
    def __init__(self, renderer: Renderer, dimensions_width: int,
                 dimensions_height: int, gap_coefficient: float) -> None:
        self.renderer = renderer
        self.dimensions_width = dimensions_width
        self.gap_coefficient = gap_coefficient
        self.obstacles: list[Obstacle] = []
        self.obstacle_history: list[str] = []
        self.clouds: list[Cloud] = []
        self.cloud_speed = settings.RUNNER['bg_cloud_speed']
        self.cloud_frequency = settings.RUNNER['cloud_frequency']
        self.horizon_lines = [HorizonLine(renderer)]
        self.night_mode = NightMode(renderer, dimensions_height)
        self.add_cloud()

    # ------------------------------------------------------------------
    def update(self, delta_time: float, current_speed: float,
               update_obstacles: bool, show_night_mode: bool) -> None:
        for line in self.horizon_lines:
            line.update(delta_time, current_speed)

        self.night_mode.update(show_night_mode)
        self.update_clouds(delta_time, current_speed)

        if update_obstacles:
            self.update_obstacles(delta_time, current_speed)

    # ------------------------------------------------------------------
    def update_clouds(self, delta_time: float, speed: float) -> None:
        el_speed = self.cloud_speed / 1000 * delta_time * speed
        for cloud in self.clouds:
            cloud.update(el_speed)

        if self.clouds:
            last_cloud = self.clouds[-1]
            if (len(self.clouds) < settings.RUNNER['max_clouds']
                    and (self.dimensions_width - last_cloud.x_pos)
                    > last_cloud.gap
                    and self.cloud_frequency > random.random()):
                self.add_cloud()
        else:
            self.add_cloud()

        self.clouds = [c for c in self.clouds if not c.remove]

    # ------------------------------------------------------------------
    def update_obstacles(self, delta_time: float, current_speed: float) -> None:
        updated = list(self.obstacles)
        for obstacle in self.obstacles:
            obstacle.update(delta_time, current_speed)
            if obstacle.remove:
                updated.pop(0)
        self.obstacles = updated

        if self.obstacles:
            last_obstacle = self.obstacles[-1]
            if (not last_obstacle.following_obstacle_created
                    and last_obstacle.is_visible()
                    and (last_obstacle.x_pos + last_obstacle.width
                         + last_obstacle.gap) < self.dimensions_width):
                self.add_new_obstacle(current_speed)
                last_obstacle.following_obstacle_created = True
        else:
            self.add_new_obstacle(current_speed)

    # ------------------------------------------------------------------
    def add_new_obstacle(self, current_speed: float) -> None:
        types = settings.OBSTACLE_TYPES
        obstacle_count = len(types) - 1
        obstacle_type = (types[random.randint(0, obstacle_count)]
                         if obstacle_count > 0 else types[0])

        # 避免连续同类型，或速度不足时换一种
        if ((obstacle_count > 0 and self._duplicate_obstacle_check(
                obstacle_type['type']))
                or current_speed < obstacle_type['min_speed']):
            self.add_new_obstacle(current_speed)
            return

        self.obstacles.append(Obstacle(
            self.renderer, obstacle_type, self.dimensions_width,
            self.gap_coefficient, current_speed))

        self.obstacle_history.insert(0, obstacle_type['type'])
        if len(self.obstacle_history) > 1:
            self.obstacle_history = self.obstacle_history[
                :settings.RUNNER['max_obstacle_duplication']]

    def _duplicate_obstacle_check(self, next_type: str) -> bool:
        duplicate_count = 0
        for obstacle_type in self.obstacle_history:
            duplicate_count = duplicate_count + 1 \
                if obstacle_type == next_type else 0
        return duplicate_count >= settings.RUNNER['max_obstacle_duplication']

    # ------------------------------------------------------------------
    def add_cloud(self) -> None:
        self.clouds.append(Cloud(self.renderer, self.dimensions_width))

    def remove_first_obstacle(self) -> None:
        self.obstacles.pop(0)

    def draw(self) -> None:
        for line in self.horizon_lines:
            line.draw()
        self.night_mode.draw()
        for cloud in self.clouds:
            cloud.draw()
        for obstacle in self.obstacles:
            obstacle.draw()

    def reset(self) -> None:
        self.obstacles = []
        for line in self.horizon_lines:
            line.reset()
        self.night_mode.reset()
