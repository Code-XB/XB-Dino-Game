"""游戏主循环 —— 1:1 移植自官方 offline.ts 的 Runner 类。

移植要点（与 Chromium 源码一一对应）：
- 世界滚动在 activated 之前保持静止（第一次跳起时游戏尚未"激活"）
- 第一次跳跃落地后触发开场动画：可视区域 44px -> 600px（CSS intro 动画）
- 距离累加 speed * deltaTime / msPerFrame，速度每帧 +0.001，上限 13
- 每 700 分切换昼夜；夜间保持 12s 后淡回白天
- 撞击后 1.2s 内允许空格重开，Enter 可立即重开
"""

from __future__ import annotations

import math
import time

import pygame

from . import settings
from .assets import Renderer, find_icon
from .audio import AudioManager
from .collision import check_for_collision
from .entities.horizon import Horizon
from .entities.trex import Trex
from .storage import load_high_score, save_high_score
from .ui.distance_meter import DistanceMeter
from .ui.game_over_panel import GameOverPanel

JUMP_KEYS = (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
DUCK_KEYS = (pygame.K_DOWN, pygame.K_s)
RESTART_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)

# CSS: .runner-container 宽 44px -> 600px，0.4s ease-out
_INTRO_CSS_DURATION = 400.0
# CSS: transition: filter 1.5s cubic-bezier(0.65, 0.05, 0.36, 1)
_INVERT_TRANSITION = 1500.0


def now_ms() -> int:
    return time.monotonic_ns() // 1_000_000


def _bezier(t: float, p1: float, p2: float) -> float:
    """三次贝塞尔（首尾控制点为 0/1）单坐标求值。"""
    mt = 1.0 - t
    return 3 * mt * mt * t * p1 + 3 * mt * t * t * p2 + t * t * t


def cubic_bezier(progress: float, x1: float, y1: float,
                 x2: float, y2: float) -> float:
    """求 CSS cubic-bezier(x1,y1,x2,y2) 在给定时间进度处的输出值。"""
    if progress <= 0:
        return 0.0
    if progress >= 1:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(24):
        mid = (lo + hi) / 2
        if _bezier(mid, x1, x2) < progress:
            lo = mid
        else:
            hi = mid
    return _bezier((lo + hi) / 2, y1, y2)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class DinoGame:
    def __init__(self, scale: float = 1.0, muted: bool = False,
                 headless: bool = False) -> None:
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass

        self.scale = max(0.5, scale)
        self.headless = headless
        size = (round(settings.CANVAS_W * self.scale),
                round(settings.CANVAS_H * self.scale))
        flags = 0
        # 窗口/任务栏图标（须在 set_mode 之前设置才能生效到任务栏）
        icon_path = find_icon()
        if icon_path:
            try:
                pygame.display.set_icon(
                    pygame.image.load(icon_path).convert_alpha())
            except pygame.error:
                pass
        self.window = pygame.display.set_mode(size, flags)
        pygame.display.set_caption('T-Rex Runner · Google Chrome 小恐龙')
        self.clock = pygame.time.Clock()

        self.renderer = Renderer()
        self.audio = AudioManager()
        self.audio.muted = muted

        self.trex = Trex(self.renderer)
        self.horizon = Horizon(self.renderer, settings.WIDTH,
                               settings.HEIGHT,
                               settings.RUNNER['gap_coefficient'])
        self.distance_meter = DistanceMeter(self.renderer,
                                            settings.WIDTH)
        self.game_over_panel: GameOverPanel | None = None

        # 存档中的最高分（官方 initializeHighScore）
        self.highest_score = 0
        loaded = load_high_score()
        if loaded > self.highest_score:
            self.highest_score = math.ceil(loaded)
        self.distance_meter.set_high_score(self.highest_score)

        # --- 运行状态 ---------------------------------------------------
        self.playing = False
        self.activated = False        # 开场动画完成后才为 True
        self.crashed = False
        self.paused = False
        self.playing_intro = False
        self.running = True
        self._had_focus = False       # 键盘焦点是否获得过（失焦暂停用）
        self._focus_paused = False    # 因失焦而暂停（回窗自动恢复）
        self._held_jump: set[int] = set()   # 当前按住的跳跃键

        self.running_time = 0.0
        self.distance_ran = 0.0
        self.current_speed = float(settings.RUNNER['speed'])
        self.time = now_ms()
        self._now = self.time
        self.digits_visible = True

        # --- 昼夜状态 ---------------------------------------------------
        self.inverted = False
        self.invert_trigger = False
        self.invert_timer = 0.0
        self.is_dark_mode = False
        self._filter_value = 0.0      # 0=日间 1=夜间（对应 CSS filter 进度）
        self._filter_from = 0.0
        self._filter_to = 0.0
        self._filter_start = 0

        # --- 开场容器宽度 -------------------------------------------------
        self.container_width = float(settings.TREX['width'])
        self._intro_start = 0
        self._intro_from = self.container_width

        # 首帧画面
        self.horizon.update(0, 0, True, False)
        self.trex.update(0)

    # ==================================================================
    # 主循环
    # ==================================================================
    def run(self) -> None:
        frame_time = now_ms()
        while self.running:
            self._handle_events()
            self._handle_held_keys()
            self._handle_focus_loss()

            now = now_ms()
            delta = min(now - frame_time, 100)   # 防止窗口卡顿后跳跃过大
            frame_time = now

            # 注意：self.time 保存官方语义（开始/死亡/重开时刻），
            # 供"死亡后 1.2s 才允许空格重开"判定使用，不能在此覆盖
            self.update(delta, now)
            self.draw()
            self.clock.tick(settings.FPS)

        pygame.quit()

    # ==================================================================
    # 事件
    # ==================================================================
    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.on_key_down(event.key)
            elif event.type == pygame.KEYUP:
                self.on_key_up(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.on_click(event.pos)
            elif event.type == pygame.WINDOWFOCUSLOST:
                # 对应官方 blur：失焦即暂停
                self._pause_on_blur()
            elif event.type == pygame.WINDOWFOCUSGAINED:
                # 对应官方 FOCUS：恢复活动窗口自动继续（官方 onVisibilityChange）
                self._resume_on_focus()

    def _handle_held_keys(self) -> None:
        """按住跳跃键连续跳。

        浏览器版本依赖系统按键自动重复（按住时持续派发 keydown），
        pygame 默认不重复派发，因此自己跟踪按住的键：恐龙一旦落地
        且跳跃键仍被按住，立即再次起跳。"""
        if (not self._held_jump or not self.playing or self.crashed
                or self.paused or self.trex.jumping or self.trex.ducking):
            return
        self.audio.play('button_press')
        self.trex.start_jump(self.current_speed)

    def _handle_focus_loss(self) -> None:
        """每帧轮询键盘焦点（官方 blur/FOCUS 监听的桌面等价、兜底）：
        失焦暂停；重新获得焦点后自动继续。"""
        if pygame.key.get_focused():
            self._resume_on_focus()
            self._had_focus = True
        else:
            self._pause_on_blur()

    def _pause_on_blur(self) -> None:
        """对应官方 blur：失焦暂停（记录标记，回窗后自动恢复）。"""
        if self.playing and self._had_focus:
            self._focus_paused = True
            self.stop()

    def _resume_on_focus(self) -> None:
        """对应官方 FOCUS：恢复活动窗口自动继续；
        只恢复"失焦导致的暂停"，P 主动暂停的保持不变。"""
        if self._focus_paused:
            self._focus_paused = False
            if self.paused and not self.crashed:
                self.trex.reset()
                self.play()

    def on_key_down(self, key: int) -> None:
        if key in JUMP_KEYS:
            self._held_jump.add(key)
        if key == pygame.K_ESCAPE:
            self.running = False
            return
        if key == pygame.K_m:
            self.audio.toggle_mute()
            return
        if key == pygame.K_p:
            if self.playing:
                self.stop()
            elif self.paused and not self.crashed:
                self.play()
            return

        if self.crashed or self.paused:
            return

        if key in JUMP_KEYS:
            if not self.playing:
                # 第一次按键：开始游戏（对应官方 setPlayStatus(true) + update()）
                self.playing = True
                self.time = self._now
                self.update(0)
            if not self.trex.jumping and not self.trex.ducking:
                self.audio.play('button_press')
                self.trex.start_jump(self.current_speed)
        elif key in DUCK_KEYS and self.playing:
            if self.trex.jumping:
                # 只有松开跳跃键时才触发快速下落
                self.trex.set_speed_drop()
            elif not self.trex.jumping and not self.trex.ducking:
                self.trex.set_duck(True)

    def on_key_up(self, key: int) -> None:
        self._held_jump.discard(key)
        if key in JUMP_KEYS and self.is_running():
            self.trex.end_jump()
        elif key in DUCK_KEYS:
            self.trex.speed_drop = False
            self.trex.set_duck(False)
        elif self.crashed:
            elapsed = self._now - self.time
            if (key in RESTART_KEYS
                    or (key in JUMP_KEYS
                        and elapsed >= settings.RUNNER['gameover_clear_time'])):
                self.restart()
        elif self.paused and key in JUMP_KEYS:
            self.trex.reset()
            self.play()

    def on_click(self, pos: tuple[int, int]) -> None:
        if not self.crashed or self.game_over_panel is None:
            return
        x = pos[0] / self.scale / settings.SCALE
        y = pos[1] / self.scale / settings.SCALE
        if self.game_over_panel.button_rect().collidepoint(x, y):
            self.restart()

    def is_running(self) -> bool:
        return self.playing and not self.crashed

    # ==================================================================
    # 更新
    # ==================================================================
    def update(self, delta_time: float, now: int | None = None) -> None:
        self._now = now_ms() if now is None else now

        if self.playing:
            if self.trex.jumping:
                self.trex.update_jump(delta_time)

            self.running_time += delta_time
            has_obstacles = self.running_time > settings.RUNNER['clear_time']

            # 第一次跳跃落地后播放开场动画
            if self.trex.jump_count == 1 and not self.playing_intro:
                self.play_intro()

            if self.playing_intro:
                # 开场期间世界静止
                self.horizon.update(0, self.current_speed,
                                    has_obstacles, False)
                self._update_intro_width()
            elif not self.crashed:
                show_night_mode = self.is_dark_mode != self.inverted
                world_dt = delta_time if self.activated else 0
                self.horizon.update(world_dt, self.current_speed,
                                    has_obstacles, show_night_mode)

            first_obstacle = (self.horizon.obstacles[0]
                              if self.horizon.obstacles else None)
            collision = bool(
                has_obstacles and first_obstacle
                and check_for_collision(first_obstacle, self.trex))

            if not collision:
                self.distance_ran += (self.current_speed * delta_time
                                      / settings.MS_PER_FRAME)
                if self.current_speed < settings.RUNNER['max_speed']:
                    self.current_speed += settings.RUNNER['acceleration']
            else:
                self.game_over()

            play_sound, self.digits_visible = self.distance_meter.update(
                delta_time, math.ceil(self.distance_ran))
            if play_sound:
                self.audio.play('score')

            self._update_night_mode(delta_time)

        if self.playing or (not self.activated
                            and self.trex.blink_count
                            < settings.RUNNER['max_blink_count']):
            self.trex.update(delta_time)

        if self.crashed and self.game_over_panel is not None:
            self.game_over_panel.update(delta_time)

        self._update_filter()

    # ------------------------------------------------------------------
    def _update_night_mode(self, delta_time: float) -> None:
        if self.invert_timer > settings.RUNNER['invert_fade_duration']:
            self.invert_timer = 0
            self.invert_trigger = False
            self.invert(True)
        elif self.invert_timer:
            self.invert_timer += delta_time
        else:
            actual_distance = self.distance_meter.get_actual_distance(
                math.ceil(self.distance_ran))
            if actual_distance > 0:
                self.invert_trigger = not (
                    actual_distance % settings.RUNNER['invert_distance'])
                if self.invert_trigger and self.invert_timer == 0:
                    self.invert_timer += delta_time
                    self.invert(False)

    def invert(self, reset: bool) -> None:
        """对应官方 invert()：切换 .inverted 类（CSS filter 过渡 1.5s）。"""
        if reset:
            self.inverted = False
            self.invert_timer = 0.0
        else:
            self.inverted = self.invert_trigger
        self._set_filter_target(1.0 if self.inverted else 0.0)

    def _set_filter_target(self, target: float) -> None:
        if target == self._filter_to:
            return
        self._filter_from = self._filter_value
        self._filter_to = target
        self._filter_start = self._now

    def _update_filter(self) -> None:
        if self._filter_value == self._filter_to:
            return
        progress = ((self._now - self._filter_start)
                    / _INVERT_TRANSITION)
        if progress >= 1:
            self._filter_value = self._filter_to
            return
        eased = cubic_bezier(progress, 0.65, 0.05, 0.36, 1)
        self._filter_value = _lerp(self._filter_from, self._filter_to, eased)

    # ------------------------------------------------------------------
    def play_intro(self) -> None:
        if not self.activated and not self.crashed:
            self.playing_intro = True
            self.trex.playing_intro = True
            self._intro_start = self._now
            self._intro_from = self.container_width
            self.playing = True
            self.activated = True
        elif self.crashed:
            self.restart()

    def _update_intro_width(self) -> None:
        progress = min(1.0, (self._now - self._intro_start)
                       / _INTRO_CSS_DURATION)
        eased = cubic_bezier(progress, 0.0, 0.0, 0.58, 1.0)
        self.container_width = _lerp(self._intro_from,
                                     settings.WIDTH, eased)
        if progress >= 1:
            self.container_width = float(settings.WIDTH)
            self.start_game()

    def start_game(self) -> None:
        self.running_time = 0
        self.playing_intro = False
        self.trex.playing_intro = False

    # ==================================================================
    # 游戏状态切换
    # ==================================================================
    def game_over(self) -> None:
        self.audio.play('hit')
        self.stop()
        self.crashed = True
        self.distance_meter.achievement = False

        self.trex.stop_crash()

        if self.game_over_panel is None:
            self.game_over_panel = GameOverPanel(
                self.renderer,
                pygame.Rect(0, 0, settings.WIDTH, settings.HEIGHT))
        self.game_over_panel.draw()

        # 刷新最高分
        if self.distance_ran > self.highest_score:
            self.highest_score = math.ceil(self.distance_ran)
            self.distance_meter.set_high_score(self.highest_score)
            save_high_score(self.highest_score)

        self.time = self._now

    def stop(self) -> None:
        self.playing = False
        self.paused = True
        # 清空按住的跳跃键，防止恢复后因"仍按住"而意外起跳
        self._held_jump.clear()

    def play(self) -> None:
        if not self.crashed:
            self.playing = True
            self.paused = False
            self.trex.update(0, self.trex.RUNNING)
            self.time = self._now

    def restart(self) -> None:
        if self.playing:
            return
        self.running_time = 0
        self.playing = True
        self.paused = False
        self.crashed = False
        self.distance_ran = 0
        self.current_speed = float(settings.RUNNER['speed'])
        self.time = self._now

        self.distance_meter.reset()
        self.horizon.reset()
        self.trex.reset()
        self.audio.play('button_press')
        self.invert(True)

        if self.game_over_panel is not None:
            self.game_over_panel.reset()
        self.update(0)

    # ==================================================================
    # 绘制
    # ==================================================================
    def draw(self) -> None:
        blend = self._filter_value
        if blend <= 0.001:
            self._draw_scene('day')
        elif blend >= 0.999:
            self._draw_scene('night')
        else:
            self._draw_scene('day')
            self._draw_scene('night')

        surface = self.renderer.composite(blend)
        self._present(surface)

    def _draw_scene(self, mode: str) -> None:
        self.renderer.begin(mode)
        self.horizon.draw()
        self.trex.draw()
        self.distance_meter.draw(self.digits_visible)
        if self.crashed and self.game_over_panel is not None:
            self.game_over_panel.draw()

    def _present(self, surface: pygame.Surface) -> None:
        # 容器宽度（开场时 44px，随后展开到 600px；溢出部分被裁剪）
        visible_w = int(round(min(self.container_width, settings.WIDTH)
                              * settings.SCALE))
        visible_w = max(settings.SCALE, visible_w)
        area = pygame.Rect(0, 0, visible_w, settings.CANVAS_H)

        t = self._filter_value
        self.window.fill(tuple(
            round(_lerp(settings.BG_COLOR_DAY[i],
                        settings.BG_COLOR_NIGHT[i], t)) for i in range(3)))

        if self.scale == 1.0:
            self.window.blit(surface, (0, 0), area)
        else:
            target = (round(area.width * self.scale),
                      round(area.height * self.scale))
            scaled = pygame.transform.scale(surface.subsurface(area), target)
            self.window.blit(scaled, (0, 0))

        pygame.display.flip()
