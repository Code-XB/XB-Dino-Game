"""最高分持久化（对应原版 Chrome Profile 中保存的 highestScore）。

存档位置优先级：
1. 环境变量 DINO_SCORE_FILE（预览/测试重定向用）
2. 打包运行（frozen）： %APPDATA%/XB-Dino-Game/highscore.json
   （安装到 Program Files 后应用目录只读，必须写到用户目录）
3. 源码运行：项目根目录 highscore.json
"""

from __future__ import annotations

import json
import os
import sys


def _default_score_file() -> str:
    if getattr(sys, 'frozen', False):
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        return os.path.join(base, 'XB-Dino-Game', 'highscore.json')
    return os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        'highscore.json')


SCORE_FILE = os.environ.get('DINO_SCORE_FILE') or _default_score_file()


def load_high_score() -> int:
    try:
        with open(SCORE_FILE, encoding='utf-8') as f:
            return int(json.load(f).get('high_score', 0))
    except (OSError, ValueError, TypeError):
        return 0


def save_high_score(score: int) -> None:
    try:
        os.makedirs(os.path.dirname(SCORE_FILE), exist_ok=True)
        with open(SCORE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'high_score': int(score)}, f)
    except OSError:
        pass
