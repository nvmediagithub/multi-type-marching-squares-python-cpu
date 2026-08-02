"""Cross-platform font loading with fallback chain.

Returns a tuple of (small, medium, large, x-large, xx-large) pygame Font objects.
"""
from __future__ import annotations

import os

import pygame


_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]

_SYS_FONT_FALLBACKS = ["DejaVu Sans", "Liberation Sans", "FreeSans", "Arial"]


def load_fonts() -> tuple[
    pygame.font.Font,
    pygame.font.Font,
    pygame.font.Font,
    pygame.font.Font,
    pygame.font.Font,
]:
    """Load fonts with a robust fallback strategy.

    Returns (size_12, size_14, size_17, size_21, size_26).
    The last element in the tuple is the largest font; used for titles.
    """
    # Try file-based fonts first
    for path in _FONT_PATHS:
        if os.path.exists(path):
            try:
                return (
                    pygame.font.Font(path, 12),
                    pygame.font.Font(path, 14),
                    pygame.font.Font(path, 17),
                    pygame.font.Font(path, 21),
                    pygame.font.Font(path, 26),
                )
            except Exception:
                continue

    # Fall back to system fonts (check Cyrillic support)
    for name in _SYS_FONT_FALLBACKS:
        try:
            f = pygame.font.SysFont(name, 14)
            if f.render("Тест", True, (0, 0, 0)).get_width() > 10:
                return (
                    pygame.font.SysFont(name, 12),
                    pygame.font.SysFont(name, 14),
                    pygame.font.SysFont(name, 17),
                    pygame.font.SysFont(name, 21),
                    pygame.font.SysFont(name, 26),
                )
        except Exception:
            continue

    # Last resort: Pygame default font
    return (
        pygame.font.Font(None, 15),
        pygame.font.Font(None, 17),
        pygame.font.Font(None, 20),
        pygame.font.Font(None, 24),
        pygame.font.Font(None, 28),
    )
