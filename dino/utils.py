"""通用工具函数。"""

from __future__ import annotations

import math
import time


def js_round(value: float) -> int:
    """JS Math.round 语义（.5 恒向 +∞ 取整，与 Python 内置 round 不同）。"""
    return math.floor(value + 0.5)


def now_ms() -> int:
    return time.monotonic_ns() // 1_000_000
