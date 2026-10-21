"""分数显示 —— 1:1 移植自官方 distance_meter.ts。"""

from __future__ import annotations

from .. import settings
from ..assets import Renderer
from ..utils import js_round


class DistanceMeter:
    def __init__(self, renderer: Renderer, canvas_width: int) -> None:
        self.renderer = renderer
        self.max_score_units = settings.METER['max_distance_units']
        self.high_score = ''
        self.achievement = False

        self.flash_timer = 0.0
        self.flash_iterations = 0

        self.digits: list[int] = []
        self.default_string = ''
        self.max_score = 0
        self.x = self._calc_x_pos(canvas_width)
        self.y = settings.METER['y']
        self._init()

    # ------------------------------------------------------------------
    def _init(self) -> None:
        """初始化为 '00000'（对应官方 init()）。"""
        max_distance_str = ''
        for _ in range(self.max_score_units):
            self.default_string += '0'
            max_distance_str += '9'
        self.max_score = int(max_distance_str)
        self.digits = [int(c) for c in self.default_string]

    def _calc_x_pos(self, canvas_width: int) -> int:
        dest_width = settings.METER['dest_width']
        return canvas_width - dest_width * (self.max_score_units + 1)

    def get_actual_distance(self, distance: float) -> int:
        return (js_round(distance * settings.METER['coefficient'])
                if distance else 0)

    # ------------------------------------------------------------------
    def update(self, delta_time: float, distance: float
               ) -> tuple[bool, bool]:
        """推进计分状态。

        返回 (是否播放达成音效, 本帧是否绘制分数)。
        绘制被拆分到 draw()，以便昼夜两套画布各绘制一次。
        """
        paint = True
        play_sound = False

        if not self.achievement:
            distance = self.get_actual_distance(distance)

            # 分数溢出初始位数时扩展一位（官方上限：只扩展一次）
            if (distance > self.max_score
                    and self.max_score_units
                    == settings.METER['max_distance_units']):
                self.max_score_units += 1
                self.max_score = int(str(self.max_score) + '9')

            if distance > 0:
                # 每 100 分：闪烁 + 音效
                if distance % settings.METER['achievement_distance'] == 0:
                    self.achievement = True
                    self.flash_timer = 0
                    play_sound = True

                distance_str = (self.default_string + str(distance))[
                    -self.max_score_units:]
                self.digits = [int(c) for c in distance_str]
            else:
                self.digits = [int(c) for c in self.default_string]
        else:
            # 达成动画：分数闪烁（短暂消失再出现）
            if self.flash_iterations <= settings.METER['flash_iterations']:
                self.flash_timer += delta_time
                if self.flash_timer < settings.METER['flash_duration']:
                    paint = False
                elif (self.flash_timer
                      > settings.METER['flash_duration'] * 2):
                    self.flash_timer = 0
                    self.flash_iterations += 1
            else:
                self.achievement = False
                self.flash_iterations = 0
                self.flash_timer = 0

        return play_sound, paint

    # ------------------------------------------------------------------
    def draw(self, paint: bool = True) -> None:
        if paint:
            for i in range(len(self.digits) - 1, -1, -1):
                self.renderer.draw(f'digit_{self.digits[i]}',
                                   self.x + i * settings.METER['dest_width'],
                                   self.y)
        self._draw_high_score()

    def _draw_high_score(self) -> None:
        if not self.high_score:
            return
        # 官方以 0.8 全局透明度绘制
        alpha = round(settings.METER['high_score_alpha'] * 255)
        high_score_x = (self.x - (self.max_score_units * 2)
                        * settings.METER['digit_width'])
        dest_width = settings.METER['dest_width']
        for i in range(len(self.high_score) - 1, -1, -1):
            char = self.high_score[i]
            if char == ' ':
                continue
            index = 10 + 'HI'.index(char) if char in 'HI' else int(char)
            self.renderer.draw(f'char_{index}',
                               high_score_x + i * dest_width,
                               self.y, alpha=alpha)

    # ------------------------------------------------------------------
    def set_high_score(self, distance: float) -> None:
        distance = self.get_actual_distance(distance)
        high_score_str = (self.default_string + str(distance))[
            -self.max_score_units:]
        self.high_score = 'HI ' + high_score_str

    def reset(self) -> None:
        self.update(0, 0)
        self.achievement = False
