"""精灵图资源加载、裁剪与画布合成。

使用 Chromium 官方离线页精灵图（offline-sprite-2x.png，即 IS_HIDPI 分支
使用的 200% 资源）。裁剪矩形直接采用官方 hdpi 坐标（本身就是 2x 图上的
像素坐标），绘制时窗口坐标按 settings.SCALE(=2) 由逻辑坐标换算。

夜间模式：官方对 canvas 施加 `filter: invert(1)`。这里预先生成整张反色
精灵图（保留 alpha），并维护日/夜两张画布，切换时按 CSS 过渡曲线做交叉
淡化 —— 因为精灵本身是灰阶，逐像素线性插值等价于 CSS 对 invert 插值。
"""

from __future__ import annotations

import os
import sys

import pygame

from . import settings

_ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
SHEET_2X_PATH = os.path.join(_ASSET_DIR, 'sprites', 'offline-sprite-2x.png')


def find_icon() -> str | None:
    """定位 icon.ico：优先可执行文件旁（打包后），其次项目根目录。"""
    candidates = []
    if getattr(sys, 'frozen', False):
        candidates.append(os.path.join(os.path.dirname(sys.executable),
                                       'icon.ico'))
    candidates.append(os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                   'icon.ico'))
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None

# 背景色（canvas 自身填充色，夜间即为 #f7f7f7 的 CSS 反色结果）
BACKGROUND = {'day': settings.BG_COLOR_DAY, 'night': settings.BG_COLOR_NIGHT}

# ---------------------------------------------------------------------------
# 裁剪矩形（2x 图像素坐标，即官方 spriteDefinition.hdpi）
# ---------------------------------------------------------------------------
_DIGIT_X = 1294
_DIGIT_W = 2 * settings.METER['digit_width']       # 20
_DIGIT_H = 2 * settings.METER['digit_height']      # 26

SINGLE_RECTS: dict[str, tuple[int, int, int, int]] = {
    # 云朵 cloud: hdpi {x:166, y:2}，逻辑 46x14
    'cloud': (166, 2, 92, 28),
    # GAME OVER 文字：textSprite {x:1294, y:2} + (textX=0, textY=13, 191x11)
    'game_over': (1294, 2 + 2 * 13, 382, 22),
    # 地平线两段 lines {sourceX:2, sourceY:52, 600x12}（HIDPI: source*=2）
    'horizon_0': (4, 104, 1200, 24),
    'horizon_1': (1204, 104, 1200, 24),
    # 数字 0-9（textSprite {x:1294,y:2}，每字符逻辑 10x13）
    **{f'digit_{v}': (_DIGIT_X + _DIGIT_W * v, 2, _DIGIT_W, _DIGIT_H)
       for v in range(10)},
    # 计分器用到的字符：0-9 直接映射，10='H'，11='I'
    **{f'char_{v}': (_DIGIT_X + _DIGIT_W * v, 2, _DIGIT_W, _DIGIT_H)
       for v in range(10)},
    'char_10': (_DIGIT_X + _DIGIT_W * 10, 2, _DIGIT_W, _DIGIT_H),
    'char_11': (_DIGIT_X + _DIGIT_W * 11, 2, _DIGIT_W, _DIGIT_H),
}

# 序列帧（列表索引即帧号）
SEQUENCE_RECTS: dict[str, list[tuple[int, int, int, int]]] = {
    # 翼龙 pterodactyl: hdpi {x:260, y:2}，逻辑 46x40，2 帧
    'pterodactyl': [(260, 2, 92, 80), (352, 2, 92, 80)],
    # 小仙人掌 cactusSmall: hdpi {x:446, y:2}，帧宽 17/34/51（1/2/3 株）
    'cactus_small': [(446, 2, 34, 70), (480, 2, 68, 70), (548, 2, 102, 70)],
    # 大仙人掌 cactusLarge: hdpi {x:652, y:2}，帧宽 25/50/75
    'cactus_large': [(652, 2, 50, 100), (702, 2, 100, 100), (802, 2, 150, 100)],
    # 月相 moon: hdpi {x:954, y:2}，逻辑 20x40，偏移 PHASES*2
    #   phase == 3 为满月，源图宽 40 逻辑像素（IS_HIDPI 下 80）
    'moon': [(954 + 2 * off, 2, 80 if i == 3 else 40, 80)
             for i, off in enumerate(settings.MOON_PHASES)],
    # T-Rex 站立/跑动/死亡帧：tRex hdpi {x:1678, y:2}，逻辑 44x47
    #   偏移 0=跳跃/站立  44=眨眼  88/132=跑动  176=站立  220=死亡
    'trex': [(1678 + 2 * off, 2, 88, 94) for off in (0, 44, 88, 132, 176, 220)],
    # T-Rex 下蹲帧：偏移 264/323，逻辑 59x47
    'trex_duck': [(1678 + 2 * off, 2, 118, 94) for off in (264, 323)],
    # 重新开始按钮 8 帧动画 restart hdpi {x:2, y:130}，逻辑 36x32
    'restart': [(2 + 2 * off, 130, 72, 64)
                for off in settings.GAME_OVER_PANEL['restart_anim_frames']],
    # 星星两个变体（sourceY = hdpi.star.y + STAR_SIZE*2*i）
    'star': [(1276, 2 + 18 * i, 18, 18) for i in range(2)],
}


class SpriteSheet:
    """单张精灵图及其命名裁剪结果。"""

    def __init__(self, path: str) -> None:
        self.surface = pygame.image.load(path).convert_alpha()
        self.single: dict[str, pygame.Surface] = {}
        self.sequences: dict[str, list[pygame.Surface]] = {}
        self._slice()

    def _slice(self) -> None:
        self.single = {name: self._crop(rect)
                       for name, rect in SINGLE_RECTS.items()}
        self.sequences = {name: [self._crop(rect) for rect in rects]
                          for name, rects in SEQUENCE_RECTS.items()}

    def _crop(self, rect: tuple[int, int, int, int]) -> pygame.Surface:
        x, y, w, h = rect
        return self.surface.subsurface(pygame.Rect(x, y, w, h)).copy()

    @classmethod
    def load_inverted(cls, path: str) -> 'SpriteSheet':
        """生成夜间变体：RGB 反色、保留 alpha（= CSS filter: invert(1)）。"""
        sheet = cls.__new__(cls)
        sheet.surface = pygame.image.load(path).convert_alpha()
        inverted = sheet.surface.copy()
        # BLEND_RGB_SUB 只作用于 RGB 通道，alpha 原样保留
        inverted.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_SUB)
        sheet.surface = inverted
        sheet._slice()
        return sheet


class Renderer:
    """逻辑画布渲染器（日/夜双画布 + 交叉淡化合成）。"""

    def __init__(self) -> None:
        self._sheets = {
            'day': SpriteSheet(SHEET_2X_PATH),
            'night': SpriteSheet.load_inverted(SHEET_2X_PATH),
        }
        self.current = 'day'
        self._canvases = {
            key: pygame.Surface((settings.CANVAS_W, settings.CANVAS_H))
            for key in ('day', 'night')
        }
        self._composite = pygame.Surface(
            (settings.CANVAS_W, settings.CANVAS_H))

    # ------------------------------------------------------------------
    @property
    def canvas(self) -> pygame.Surface:
        return self._canvases[self.current]

    def begin(self, mode: str) -> None:
        """切换到指定配色并清空画布（相当于官方每帧的 clearCanvas）。"""
        self.current = mode
        self.canvas.fill(BACKGROUND[mode])

    # ------------------------------------------------------------------
    def draw(self, name: str, x: float, y: float, *, frame: int = 0,
             alpha: int | None = None) -> None:
        """把命名精灵绘制到当前画布的逻辑坐标 (x, y)。"""
        sheet = self._sheets[self.current]
        if name in sheet.sequences:
            frames = sheet.sequences[name]
            surf = frames[max(0, min(frame, len(frames) - 1))]
        else:
            surf = sheet.single[name]
        if alpha is not None and alpha < 255:
            surf = surf.copy()
            surf.set_alpha(alpha)
        self.canvas.blit(surf, (round(x * settings.SCALE),
                                round(y * settings.SCALE)))

    # ------------------------------------------------------------------
    def composite(self, blend: float) -> pygame.Surface:
        """返回最终画面；blend ∈ (0,1) 时按比例混合日/夜画布。"""
        if blend <= 0:
            return self._canvases['day']
        if blend >= 1:
            return self._canvases['night']
        self._composite.blit(self._canvases['day'], (0, 0))
        night = self._canvases['night']
        night.set_alpha(round(blend * 255))
        self._composite.blit(night, (0, 0))
        night.set_alpha(255)
        return self._composite
