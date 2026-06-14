from __future__ import annotations

import math
from typing import Optional

import screeninfo

from .state import CatActivityScope


class ActivitySpace:
    def __init__(self, screen_frame: tuple[float, float, float, float],
                 visible_frame: tuple[float, float, float, float],
                 dock_edge: str,
                 walk_range: tuple[float, float],
                 baseline_y: float,
                 entrance_point: tuple[float, float]):
        self.screen_frame = screen_frame  # (x, y, w, h)
        self.visible_frame = visible_frame
        self.dock_edge = dock_edge
        self.walk_range = walk_range
        self.baseline_y = baseline_y
        self.entrance_point = entrance_point

    @staticmethod
    def make(screen_frame: tuple[float, float, float, float],
             visible_frame: tuple[float, float, float, float],
             taskbar_height: float = 0,
             start_position_percent: float = 75) -> "ActivitySpace":
        sx, sy, sw, sh = screen_frame
        vx, vy, vw, vh = visible_frame

        # Determine dock edge (Windows taskbar)
        edge = "bottom_visible"
        threshold = 24
        bottom_inset = vy - sy
        left_inset = vx - sx
        right_inset = (sx + sw) - (vx + vw)

        if bottom_inset > threshold:
            edge = "bottom_visible"
        elif left_inset > threshold:
            edge = "left"
        elif right_inset > threshold:
            edge = "right"
        else:
            edge = "bottom_hidden"

        baseline_y = vy
        walk_range = (vx, vx + vw)

        normalized = max(0, min(100, start_position_percent)) / 100
        projected_x = sx + sw * normalized
        clamped_x = max(walk_range[0], min(walk_range[1], projected_x))

        return ActivitySpace(
            screen_frame=screen_frame,
            visible_frame=visible_frame,
            dock_edge=edge,
            walk_range=walk_range,
            baseline_y=baseline_y,
            entrance_point=(clamped_x, baseline_y),
        )

    def clamped_point(self, point: tuple[float, float],
                      content_size: tuple[float, float] = (0, 0),
                      scope: CatActivityScope = CatActivityScope.DOCK_EDGE) -> tuple[float, float]:
        if scope == CatActivityScope.DESKTOP:
            return self._desktop_clamped_point(point, content_size)
        return self._dock_edge_clamped_point(point, content_size[0])

    def _dock_edge_clamped_point(self, point: tuple[float, float], content_width: float = 0) -> tuple[float, float]:
        x_range = self.dock_edge_walk_range(content_width)
        x = max(x_range[0], min(x_range[1], point[0]))
        return (x, self.baseline_y)

    def walk_range_for_content(self, width: float, scope: CatActivityScope = CatActivityScope.DOCK_EDGE) -> tuple[float, float]:
        if scope == CatActivityScope.DESKTOP:
            return self._desktop_walk_range(width)
        return self.dock_edge_walk_range(width)

    def dock_edge_walk_range(self, content_width: float = 0) -> tuple[float, float]:
        safe_w = max(0, content_width)
        upper = self.walk_range[1] - safe_w
        if upper < self.walk_range[0]:
            upper = self.walk_range[0]
        return (self.walk_range[0], upper)

    def _desktop_clamped_point(self, point: tuple[float, float], content_size: tuple[float, float]) -> tuple[float, float]:
        x_range = self._desktop_walk_range(content_size[0])
        y_range = self._desktop_y_range(content_size[1])
        x = max(x_range[0], min(x_range[1], point[0]))
        y = max(y_range[0], min(y_range[1], point[1]))
        return (x, y)

    def _desktop_walk_range(self, width: float) -> tuple[float, float]:
        safe_w = max(0, width)
        upper = (self.screen_frame[0] + self.screen_frame[2]) - safe_w
        s0 = self.screen_frame[0]
        if upper < s0:
            upper = s0
        return (s0, upper)

    def _desktop_y_range(self, height: float) -> tuple[float, float]:
        safe_h = max(0, height)
        upper = (self.screen_frame[1] + self.screen_frame[3]) - safe_h
        s1 = self.screen_frame[1]
        if upper < s1:
            upper = s1
        return (s1, upper)


def get_current_activity_space(start_position_percent: float = 75) -> ActivitySpace:
    try:
        monitors = screeninfo.get_monitors()
        if not monitors:
            return ActivitySpace.make(
                (0, 0, 1920, 1080), (0, 0, 1920, 1080), taskbar_height=0, start_position_percent=start_position_percent
            )
        primary = monitors[0]
        # Get taskbar height from visible vs total geometry
        # Windows reports the full screen; we estimate taskbar from y offset
        sx, sy = primary.x, primary.y
        sw = primary.width
        sh = primary.height
        # screeninfo doesn't give visible frame directly
        # We assume taskbar at bottom by default on Windows
        # Actually, on modern Windows with auto-hide taskbar, the full screen includes taskbar
        taskbar_h = 40  # approximate
        visible_frame = (sx, sy, sw, sh - taskbar_h)
        return ActivitySpace.make(
            (sx, sy, sw, sh),
            visible_frame,
            taskbar_height=taskbar_h,
            start_position_percent=start_position_percent,
        )
    except Exception:
        return ActivitySpace.make(
            (0, 0, 1920, 1080), (0, 0, 1920, 1080), taskbar_height=0, start_position_percent=start_position_percent
        )
