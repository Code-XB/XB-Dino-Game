"""Game Over 面板 —— 1:1 移植自官方 game_over_panel.ts（含重启按钮动画）。"""

from __future__ import annotations

import pygame

from .. import settings
from ..assets import Renderer

PANEL = settings.GAME_OVER_PANEL


class GameOverPanel:
    def __init__(self, renderer: Renderer, canvas_dimensions: pygame.Rect
                 ) -> None:
        self.renderer = renderer
        self.canvas_dimensions = canvas_dimensions
        self.current_frame = 0
        self.anim_timer = 0.0
        # 官方行为：动画循环结束后停留在最后一帧（箭头按钮），不再重播
        self.anim_done = False
        self.ms_per_frame = (PANEL['restart_anim_duration']
                             / len(PANEL['restart_anim_frames']))

    # ------------------------------------------------------------------
    def update_dimensions(self, width: int, height: int | None = None) -> None:
        self.canvas_dimensions.width = width
        if height:
            self.canvas_dimensions.height = height
        self.current_frame = len(PANEL['restart_anim_frames']) - 1
        self.anim_done = True

    def draw(self) -> None:
        self._draw_game_over_text()
        self._draw_restart_button()

    # ------------------------------------------------------------------
    def _draw_game_over_text(self) -> None:
        cfg = PANEL
        center_x = self.canvas_dimensions.width / 2
        target_x = round(center_x - cfg['text_width'] / 2)
        target_y = round((self.canvas_dimensions.height - 25) / 3)
        self.renderer.draw('game_over', target_x, target_y)

    def _draw_restart_button(self) -> None:
        cfg = PANEL
        total = len(cfg['restart_anim_frames'])
        frame = max(0, min(self.current_frame, total - 1))
        target_x = self.canvas_dimensions.width / 2 - cfg['restart_height'] / 2
        target_y = self.canvas_dimensions.height / 2
        self.renderer.draw('restart', target_x, target_y, frame=frame)

    # ------------------------------------------------------------------
    def update(self, delta_time: float) -> None:
        """重启按钮动画：logo 静置 -> 快速旋转 -> 停在箭头按钮（官方 reset()
        只停止动画循环、不再重绘，画面因此保留最后一帧）。"""
        if self.anim_done:
            return
        self.anim_timer += delta_time
        total_frames = len(PANEL['restart_anim_frames'])

        if (self.current_frame == 0
                and self.anim_timer > PANEL['logo_pause_duration']):
            self.anim_timer = 0
            self.current_frame = 1
        elif 0 < self.current_frame < total_frames:
            if self.anim_timer >= self.ms_per_frame:
                self.anim_timer = 0
                self.current_frame += 1
                if self.current_frame >= total_frames:
                    # 动画结束：固定在最后一帧
                    self.current_frame = total_frames - 1
                    self.anim_done = True

    def button_rect(self) -> pygame.Rect:
        """重启按钮的点击热区（逻辑坐标）。"""
        cfg = PANEL
        return pygame.Rect(
            round(self.canvas_dimensions.width / 2 - cfg['restart_height'] / 2),
            round(self.canvas_dimensions.height / 2),
            cfg['restart_width'], cfg['restart_height'])

    def reset(self) -> None:
        self.anim_timer = 0
        self.current_frame = 0
        self.anim_done = False
