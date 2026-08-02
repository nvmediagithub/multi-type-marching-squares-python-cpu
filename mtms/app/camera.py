"""Camera state for map view — pan and zoom."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Camera:
    """Holds 2D offset and zoom factor for the terrain map viewport."""
    x: float = 0.0
    y: float = 0.0
    zoom: float = 1.0

    def update_pan(self, dx: int, dy: int) -> None:
        """Shift camera by (dx, dy) pixels in screen space."""
        self.x += dx
        self.y += dy

    def set_pan(self, x: float, y: float) -> None:
        """Absolute camera position."""
        self.x = x
        self.y = y

    def update_zoom(
        self,
        factor: float,
        min_zoom: float = 0.2,
        max_zoom: float = 25.0,
    ) -> None:
        """Multiply zoom by `factor`, clamped to [min_zoom, max_zoom]."""
        self.zoom = max(min_zoom, min(max_zoom, self.zoom * factor))

    def reset(self) -> None:
        """Reset to default position and zoom."""
        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.0
