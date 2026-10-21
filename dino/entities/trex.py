"""T-Rex 小恐龙 —— 1:1 移植自官方 trex.ts。"""

from __future__ import annotations

import math
import random

from .. import settings
from ..assets import Renderer
from ..utils import js_round, now_ms


class Trex:
    WAITING = 'WAITING'
    RUNNING = 'RUNNING'
    JUMPING = 'JUMPING'
    CRASHED = 'CRASHED'
    DUCKING = 'DUCKING'

    # 'trex' 序列帧在精灵图中的偏移（逻辑单位，帧索引 = 偏移 // 44）
    _OFFSET_TO_INDEX = {0: 0, 44: 1, 88: 2, 132: 3, 176: 4, 220: 5}

    def __init__(self, renderer: Renderer) -> None:
        self.renderer = renderer
        self.config = dict(settings.TREX)

        # 站立 y 坐标 = 画布高 - 恐龙高 - 底部留白 = 150-47-10 = 93
        self.ground_y_pos = (settings.HEIGHT - self.config['height']
                             - settings.RUNNER['bottom_pad'])
        self.min_jump_height = self.ground_y_pos - self.config['min_jump_height']

        self.x_pos = 0.0
        self.y_pos = float(self.ground_y_pos)
        self.x_initial_pos = 0

        self.jump_velocity = 0.0
        self.jumping = False
        self.ducking = False
        self.speed_drop = False
        self.jump_count = 0
        self.reached_min_height = False
        self.playing_intro = False

        self.status = self.WAITING
        self.current_frame = 0
        self.timer = 0.0
        self.ms_per_frame = settings.MS_PER_FRAME
        self.anim_frames = [0]

        # 眨眼状态
        self.blink_count = 0
        self.blinking = False
        self.blink_delay = 0
        self.blink_timer = 0
        self.blink_wait = 0
        self._set_blink_delay()

    # ------------------------------------------------------------------
    # 逻辑更新
    # ------------------------------------------------------------------
    def update(self, delta_time: float, status: str | None = None) -> None:
        self.timer += delta_time

        if status is not None:
            self.status = status
            self.current_frame = 0
            self.timer = 0
            self.ms_per_frame = settings.TREX_ANIM_FRAMES[status]['ms_per_frame']
            self.anim_frames = settings.TREX_ANIM_FRAMES[status]['frames']

        # 开场动画：从左侧跑到 START_X_POS（官方同样对每帧增量取整）
        if self.playing_intro and self.x_pos < self.config['start_x_pos']:
            self.x_pos += js_round(
                (self.config['start_x_pos']
                 / self.config['intro_duration']) * delta_time)
            self.x_initial_pos = self.x_pos

        if self.status == self.WAITING:
            self._update_blink(delta_time)
        else:
            # 帧推进（跑动 / 下蹲动画）
            if self.timer >= self.ms_per_frame:
                self.current_frame = (0 if self.current_frame
                                      == len(self.anim_frames) - 1
                                      else self.current_frame + 1)
                self.timer = 0

        # 按住下键落地后转为下蹲
        if self.speed_drop and self.y_pos == self.ground_y_pos:
            self.speed_drop = False
            self.set_duck(True)

    # ------------------------------------------------------------------
    # 眨眼（仅待机）：随机 1~7s 眨一次，闭眼 333ms，最多 3 次
    # ------------------------------------------------------------------
    def _set_blink_delay(self) -> None:
        self.blink_delay = math.ceil(random.random() * settings.BLINK_TIMING)

    def _update_blink(self, delta_time: float) -> None:
        if self.blink_count >= settings.RUNNER['max_blink_count']:
            self.blinking = False
            return
        self.blink_timer += delta_time
        if self.blinking:
            # 闭眼持续 msPerFrame (= 1000/3 ms)
            self.blink_wait += delta_time
            if self.blink_wait >= self.ms_per_frame:
                self.blinking = False
                self.blink_count += 1
                self.blink_timer = 0
                self.blink_wait = 0
                self._set_blink_delay()
        elif self.blink_timer >= self.blink_delay:
            self.blinking = True
            self.blink_wait = 0

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------
    def draw(self) -> None:
        x = js_round(self.x_pos)
        if self.ducking and self.status != self.CRASHED:
            self.renderer.draw('trex_duck', x, self.y_pos,
                               frame=self.current_frame)
        elif self.status == self.WAITING:
            # 偏移 44=闭眼  0=睁眼
            index = 1 if self.blinking else 0
            self.renderer.draw('trex', x, self.y_pos, frame=index)
        else:
            index = self._OFFSET_TO_INDEX.get(
                self.anim_frames[self.current_frame], 0)
            self.renderer.draw('trex', x, self.y_pos, frame=index)

    # ------------------------------------------------------------------
    # 跳跃
    # ------------------------------------------------------------------
    def start_jump(self, speed: float) -> None:
        if self.jumping:
            return
        self.update(0, self.JUMPING)
        # 根据当前速度微调起跳初速
        self.jump_velocity = self.config['initial_jump_velocity'] - speed / 10
        self.jumping = True
        self.reached_min_height = False
        self.speed_drop = False

    def end_jump(self) -> None:
        if (self.reached_min_height
                and self.jump_velocity < self.config['drop_velocity']):
            self.jump_velocity = self.config['drop_velocity']

    def update_jump(self, delta_time: float) -> None:
        ms_per_frame = settings.TREX_ANIM_FRAMES[self.JUMPING]['ms_per_frame']
        frames_elapsed = delta_time / ms_per_frame

        # 快速下落
        if self.speed_drop:
            self.y_pos += js_round(self.jump_velocity
                                   * self.config['speed_drop_coefficient']
                                   * frames_elapsed)
        else:
            self.y_pos += js_round(self.jump_velocity * frames_elapsed)

        self.jump_velocity += self.config['gravity'] * frames_elapsed

        # 达到最小高度
        if self.y_pos < self.min_jump_height or self.speed_drop:
            self.reached_min_height = True

        # 达到最大高度
        if self.y_pos < self.config['max_jump_height'] or self.speed_drop:
            self.end_jump()

        # 落回地面
        if self.y_pos > self.ground_y_pos:
            self.reset()
            self.jump_count += 1

    def set_speed_drop(self) -> None:
        self.speed_drop = True
        self.jump_velocity = 1

    def set_duck(self, is_ducking: bool) -> None:
        if is_ducking and self.status != self.DUCKING:
            self.update(0, self.DUCKING)
            self.ducking = True
        elif self.status == self.DUCKING:
            self.update(0, self.RUNNING)
            self.ducking = False

    # ------------------------------------------------------------------
    def reset(self) -> None:
        self.x_pos = self.x_initial_pos
        self.y_pos = float(self.ground_y_pos)
        self.jump_velocity = 0
        self.jumping = False
        self.ducking = False
        self.update(0, self.RUNNING)
        self.speed_drop = False
        self.jump_count = 0

    def stop_crash(self) -> None:
        """gameOver(): tRex.update(100, CRASHED)；下蹲中撞击时站起 +1px。"""
        if self.ducking:
            self.x_pos += 1
            self.ducking = False
        self.update(100, self.CRASHED)
