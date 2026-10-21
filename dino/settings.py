"""全局常量与配置。

所有数值 1:1 取自 Chromium 官方源码
(chromium/src/components/neterror/resources/dino_game/)：
- constants.ts        -> FPS / DEFAULT_DIMENSIONS
- offline.ts          -> defaultBaseConfig / normalModeConfig
- trex.ts             -> defaultTrexConfig / normalJumpConfig / animFrames
- horizon.ts          -> horizonConfig
- cloud.ts            -> Config
- night_mode.ts       -> Config / PHASES
- distance_meter.ts   -> Dimensions / Config
- game_over_panel.ts  -> defaultPanelDimensions / animConfig
"""

# ---------------------------------------------------------------------------
# 基础尺寸 (constants.ts: DEFAULT_DIMENSIONS, FPS)
# ---------------------------------------------------------------------------
FPS = 60
MS_PER_FRAME = 1000 / FPS          # 16.666... 每帧毫秒数

WIDTH = 600                        # 逻辑画布宽
HEIGHT = 150                       # 逻辑画布高

# hdpi 渲染：内部画布与精灵均按 2 倍绘制（对应 IS_HIDPI 分支）
SCALE = 2
CANVAS_W = WIDTH * SCALE           # 1200
CANVAS_H = HEIGHT * SCALE          # 300

# 页面背景色 (neterror.css: #f7f7f7)；夜间模式为 CSS invert(100%) 后的颜色
BG_COLOR_DAY = (247, 247, 247)
BG_COLOR_NIGHT = (255 - 247, 255 - 247, 255 - 247)

# ---------------------------------------------------------------------------
# Runner 配置 (offline.ts: defaultBaseConfig + normalModeConfig)
# ---------------------------------------------------------------------------
RUNNER = {
    'bg_cloud_speed': 0.2,
    'bottom_pad': 10,
    'clear_time': 3000,            # 开始出障碍物的等待时间 (ms)
    'cloud_frequency': 0.5,
    'gameover_clear_time': 1200,   # 死亡后允许按键重开的时间 (ms)
    'invert_fade_duration': 12000, # 夜间模式持续时长 (ms)
    'invert_distance': 700,        # 每多少分切换昼夜
    'max_blink_count': 3,          # 待机时眨眼次数上限
    'max_clouds': 6,
    'max_obstacle_duplication': 2,
    'max_obstacle_length': 3,      # 仙人掌最多几株连排
    'acceleration': 0.001,         # 每帧加速度
    'gap_coefficient': 0.6,
    'max_speed': 13,
    'speed': 6,                    # 初速度
    'speed_drop_coefficient': 3,   # 快速下落系数
}

# ---------------------------------------------------------------------------
# T-Rex (trex.ts: defaultTrexConfig + normalJumpConfig + BLINK_TIMING)
# ---------------------------------------------------------------------------
TREX = {
    'drop_velocity': -5,
    'flash_off': 175,
    'flash_on': 100,
    'height': 47,
    'height_duck': 25,
    'intro_duration': 1500,        # 开场走位时长 (ms)
    'speed_drop_coefficient': 3,
    'sprite_width': 262,
    'start_x_pos': 50,             # 跑动时的 x 坐标
    'width': 44,
    'width_duck': 59,
    'gravity': 0.6,
    'max_jump_height': 30,
    'min_jump_height': 30,
    'initial_jump_velocity': -10,
}
BLINK_TIMING = 7000                # 眨眼随机间隔上限 (ms)

# T-Rex 动画帧（相对 tRex 精灵原点的 x 偏移，逻辑单位）
TREX_ANIM_FRAMES = {
    'WAITING':  {'frames': [44, 0],    'ms_per_frame': 1000 / 3},
    'RUNNING':  {'frames': [88, 132],  'ms_per_frame': 1000 / 12},
    'CRASHED':  {'frames': [220],      'ms_per_frame': 1000 / 60},
    'JUMPING':  {'frames': [0],        'ms_per_frame': 1000 / 60},
    'DUCKING':  {'frames': [264, 323], 'ms_per_frame': 1000 / 8},
}

# T-Rex 碰撞盒 (trex.ts: collisionBoxes)
TREX_COLLISION_BOXES = {
    'ducking': [(1, 18, 55, 25)],
    'running': [
        (22, 0, 17, 16),
        (1, 18, 30, 9),
        (10, 35, 14, 8),
        (1, 24, 29, 5),
        (5, 30, 21, 4),
        (9, 34, 15, 4),
    ],
}

# ---------------------------------------------------------------------------
# 障碍物 (offline_sprite_definitions.ts: spriteDefinitionByType.original)
# ---------------------------------------------------------------------------
MAX_GAP_COEFFICIENT = 1.5

OBSTACLE_TYPES = [
    {
        'type': 'CACTUS_SMALL',
        'width': 17, 'height': 35,
        'y_pos': 105,
        'multiple_speed': 4,
        'min_gap': 120,
        'min_speed': 0,
        'collision_boxes': [(0, 7, 5, 27), (4, 0, 6, 34), (10, 4, 7, 14)],
    },
    {
        'type': 'CACTUS_LARGE',
        'width': 25, 'height': 50,
        'y_pos': 90,
        'multiple_speed': 7,
        'min_gap': 120,
        'min_speed': 0,
        'collision_boxes': [(0, 12, 7, 38), (8, 0, 7, 49), (13, 10, 10, 38)],
    },
    {
        'type': 'PTERODACTYL',
        'width': 46, 'height': 40,
        'y_pos': [100, 75, 50],    # 三种飞行高度
        'multiple_speed': 999,
        'min_gap': 150,
        'min_speed': 8.5,
        'collision_boxes': [
            (15, 15, 16, 5), (18, 21, 24, 6), (2, 14, 4, 3),
            (6, 10, 4, 7), (10, 8, 6, 9),
        ],
        'num_frames': 2,
        'frame_rate': 1000 / 6,
        'speed_offset': 0.8,
    },
]

# ---------------------------------------------------------------------------
# 地面 (offline_sprite_definitions.ts: lines) — 两条 600x12 的地平线段
# ---------------------------------------------------------------------------
HORIZON_LINE = {
    'source_x': 2,
    'source_y': 52,
    'width': 600,
    'height': 12,
    'y_pos': 127,
    'bump_threshold': 0.5,         # horizon_line.ts: bumpThreshold
}

# ---------------------------------------------------------------------------
# 云朵 (cloud.ts: Config)
# ---------------------------------------------------------------------------
CLOUD = {
    'width': 46,
    'height': 14,
    'max_sky_level': 30,
    'min_sky_level': 71,
    'min_cloud_gap': 100,
    'max_cloud_gap': 400,
}

# ---------------------------------------------------------------------------
# 夜间模式 (night_mode.ts: Config + PHASES)
# ---------------------------------------------------------------------------
NIGHT = {
    'fade_speed': 0.035,
    'height': 40,
    'moon_speed': 0.25,
    'num_stars': 2,
    'star_size': 9,
    'star_speed': 0.3,
    'star_max_y': 70,
    'width': 20,
}
MOON_PHASES = [140, 120, 100, 60, 40, 20, 0]

# ---------------------------------------------------------------------------
# 计分器 (distance_meter.ts: Dimensions + Config)
# ---------------------------------------------------------------------------
METER = {
    'digit_width': 10,
    'digit_height': 13,
    'dest_width': 11,
    'max_distance_units': 5,
    'achievement_distance': 100,
    'coefficient': 0.025,          # 逻辑距离 -> 分数
    'flash_duration': 1000 / 4,
    'flash_iterations': 3,
    'high_score_alpha': 0.8,
    'y': 5,
}

# ---------------------------------------------------------------------------
# Game Over 面板 (game_over_panel.ts)
# ---------------------------------------------------------------------------
GAME_OVER_PANEL = {
    'text_x': 0,
    'text_y': 13,
    'text_width': 191,
    'text_height': 11,
    'restart_width': 36,
    'restart_height': 32,
    'restart_anim_frames': [0, 36, 72, 108, 144, 180, 216, 252],
    'restart_anim_duration': 875,  # RESTART_ANIM_DURATION
    'logo_pause_duration': 875,    # LOGO_PAUSE_DURATION
}
