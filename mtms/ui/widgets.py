"""Reusable Pygame UI widgets with theme injection."""
from __future__ import annotations

import pygame

from mtms.config import ThemeConfig


# Default (light) theme fallback
_DEFAULT_THEME = ThemeConfig()


class Button:
    """Clickable button with optional toggle state and hover highlighting."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        text: str,
        font: pygame.font.Font,
        toggle: bool = False,
        theme: ThemeConfig | None = None,
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.toggle = toggle
        self.active = False
        self.hovered = False
        self.clicked = False
        self.theme = theme or _DEFAULT_THEME

    def handle(self, ev: pygame.event.Event) -> None:
        """Process a single pygame event."""
        self.clicked = False
        if ev.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(ev.pos)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos):
                self.clicked = True
                if self.toggle:
                    self.active = not self.active

    def draw(self, surf: pygame.Surface) -> None:
        """Render the button on a Pygame surface."""
        th = self.theme
        if self.toggle and self.active:
            clr, tc = th.accent, th.accent_text
        elif self.hovered:
            clr, tc = th.button_hover, th.text_color
        else:
            clr, tc = th.button_color, th.text_color

        pygame.draw.rect(surf, clr, self.rect, border_radius=6)
        pygame.draw.rect(surf, th.border, self.rect, 1, border_radius=6)

        ts = self.font.render(self.text, True, tc)
        surf.blit(
            ts,
            (self.rect.x + (self.rect.w - ts.get_width()) // 2,
             self.rect.y + (self.rect.h - ts.get_height()) // 2),
        )


class Dropdown:
    """Expandable dropdown menu for selecting from a list of options."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        options: list[str],
        font: pygame.font.Font,
        selected: int = 0,
        theme: ThemeConfig | None = None,
    ):
        self.rect = pygame.Rect(rect)
        self.options = options
        self.font = font
        self.sel = selected
        self.open = False
        self.changed = False
        self.theme = theme or _DEFAULT_THEME

    def handle(self, ev: pygame.event.Event) -> None:
        """Process a single pygame event."""
        self.changed = False
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.open:
                for i in range(len(self.options)):
                    r = pygame.Rect(
                        self.rect.x,
                        self.rect.y + (i + 1) * self.rect.h,
                        self.rect.w,
                        self.rect.h,
                    )
                    if r.collidepoint(ev.pos):
                        if self.sel != i:
                            self.sel = i
                            self.changed = True
                        self.open = False
                        return
                self.open = False
                return

            if self.rect.collidepoint(ev.pos):
                self.open = True

    def draw(self, surf: pygame.Surface) -> None:
        """Render the dropdown (and expanded items if open)."""
        th = self.theme
        pygame.draw.rect(surf, th.button_color, self.rect, border_radius=6)
        pygame.draw.rect(surf, th.border, self.rect, 1, border_radius=6)

        label = str(self.options[self.sel])
        ts = self.font.render(label, True, th.text_color)
        surf.blit(
            ts,
            (self.rect.x + 8,
             self.rect.y + (self.rect.h - ts.get_height()) // 2),
        )

        # Arrow indicator
        ax = self.rect.right - 16
        ay = self.rect.centery
        pygame.draw.polygon(
            surf, th.text_secondary,
            [(ax - 3, ay - 2), (ax + 3, ay - 2), (ax, ay + 3)],
        )

        # Expanded items
        if self.open:
            for i, opt in enumerate(self.options):
                r = pygame.Rect(
                    self.rect.x,
                    self.rect.y + (i + 1) * self.rect.h,
                    self.rect.w,
                    self.rect.h,
                )
                c = th.button_hover if r.collidepoint(pygame.mouse.get_pos()) else th.panel_bg
                pygame.draw.rect(surf, c, r)
                pygame.draw.rect(surf, th.border, r, 1)
                ts = self.font.render(str(opt), True, th.text_color)
                surf.blit(ts, (r.x + 8, r.y + (r.h - ts.get_height()) // 2))
