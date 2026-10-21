"""碰撞检测 —— 1:1 移植自官方 offline.ts 的 checkForCollision / boxCompare。"""

from __future__ import annotations

from dataclasses import dataclass

from . import settings
from .entities.obstacle import Obstacle
from .entities.trex import Trex


@dataclass
class CollisionBox:
    x: int
    y: int
    width: int
    height: int

    def overlaps(self, other: 'CollisionBox') -> bool:
        """boxCompare: 轴对齐包围盒检测。"""
        return (self.x < other.x + other.width
                and self.x + self.width > other.x
                and self.y < other.y + other.height
                and self.y + self.height > other.y)


def _adjusted(box: CollisionBox, anchor: CollisionBox) -> CollisionBox:
    """createAdjustedCollisionBox：把相对盒平移到实际位置。"""
    return CollisionBox(box.x + anchor.x, box.y + anchor.y,
                        box.width, box.height)


def check_for_collision(obstacle: Obstacle | None, trex: Trex
                        ) -> tuple[CollisionBox, CollisionBox] | None:
    """返回相交的盒子对（调试用），无碰撞时返回 None。"""
    if obstacle is None or obstacle.remove:
        return None

    # 外围各留 1px 白边修正
    trex_box = CollisionBox(
        round(trex.x_pos) + 1, round(trex.y_pos) + 1,
        settings.TREX['width'] - 2, settings.TREX['height'] - 2)
    obstacle_box = CollisionBox(
        round(obstacle.x_pos) + 1, round(obstacle.y_pos) + 1,
        obstacle.type_config['width'] * obstacle.size - 2,
        obstacle.type_config['height'] - 2)

    if not trex_box.overlaps(obstacle_box):
        return None

    trex_boxes = [CollisionBox(*b) for b in (
        settings.TREX_COLLISION_BOXES['ducking'] if trex.ducking
        else settings.TREX_COLLISION_BOXES['running'])]
    obstacle_boxes = [CollisionBox(*b) for b in obstacle.collision_boxes]

    for t_box in trex_boxes:
        adj_trex = _adjusted(t_box, trex_box)
        for o_box in obstacle_boxes:
            adj_obs = _adjusted(o_box, obstacle_box)
            if adj_trex.overlaps(adj_obs):
                return adj_trex, adj_obs
    return None
