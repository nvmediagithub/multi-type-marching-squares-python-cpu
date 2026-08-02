"""Toolbar and status bar rendering."""
from __future__ import annotations

import pygame

from mtms.config import ThemeConfig, DisplayConfig
from mtms.ui.widgets import Button


class ToolbarRenderer:
    """Renders the top toolbar and bottom status bar."""

    def __init__(
        self,
        theme: ThemeConfig,
        display: DisplayConfig,
    ):
        self.theme = theme
        self.display = display

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------
    def render_toolbar(
        self,
        screen: pygame.Surface,
        buttons: list[Button],
        nav_buttons: list[Button] | None = None,
    ) -> None:
        """Draw the top toolbar area and all contained widgets."""
        th = self.theme
        bar = pygame.Rect(0, 0, screen.get_width(), self.display.ui_bar_height)
        pygame.draw.rect(screen, th.panel_bg, bar)
        pygame.draw.line(
            screen, th.border,
            (0, self.display.ui_bar_height),
            (screen.get_width(), self.display.ui_bar_height),
        )

        for btn in buttons:
            btn.draw(screen)

        if nav_buttons:
            for btn in nav_buttons:
                btn.draw(screen)

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------
    def render_status(
        self,
        screen: pygame.Surface,
        message: str,
        font: pygame.font.Font,
    ) -> None:
        """Draw the bottom status bar with a text message."""
        th = self.theme
        y = screen.get_height() - self.display.status_bar_height
        sw = screen.get_width()

        pygame.draw.rect(screen, th.panel_bg, (0, y, sw, self.display.status_bar_height))
        pygame.draw.line(screen, th.border, (0, y), (sw, y))

        ts = font.render(message, True, th.text_secondary)
        screen.blit(ts, (12, y + (self.display.status_bar_height - ts.get_height()) // 2))
