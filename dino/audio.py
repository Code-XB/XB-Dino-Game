"""音效管理。

加载 Chromium 官方三段音效（components/neterror/resources/sounds/）：
- button-press.mp3  起跳 / 重开
- score-reached.mp3 每 100 分
- hit.mp3           撞击
"""

from __future__ import annotations

import os

import pygame

_ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                          'assets', 'audio')


class AudioManager:
    def __init__(self) -> None:
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self.muted = False
        self._load('button_press', 'button-press.mp3')
        self._load('hit', 'hit.mp3')
        self._load('score', 'score-reached.mp3')

    def _load(self, key: str, filename: str) -> None:
        path = os.path.join(_ASSET_DIR, filename)
        try:
            self._sounds[key] = pygame.mixer.Sound(path)
        except pygame.error:
            self._sounds[key] = None  # type: ignore[assignment]

    def play(self, key: str) -> None:
        sound = self._sounds.get(key)
        if sound is not None and not self.muted:
            sound.play()

    def toggle_mute(self) -> bool:
        self.muted = not self.muted
        return self.muted
