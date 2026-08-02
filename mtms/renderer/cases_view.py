"""Cases view renderer — displays the 512 MTMS lookup-table configurations."""
from __future__ import annotations

import pygame

from mtms.algorithm.interpolation import compute_12_points
from mtms.algorithm.types import MTMSCase, Point2D
from mtms.config import ThemeConfig, CaseViewConfig, DisplayConfig


class CasesViewRenderer:
    """Renders the cases-view grid of 16 configurations per page."""

    def __init__(
        self,
        ms_table: dict[int, MTMSCase],
        theme: ThemeConfig,
        cases_config: CaseViewConfig,
        display: DisplayConfig,
        fonts: tuple[pygame.font.Font, pygame.font.Font, pygame.font.Font,
                     pygame.font.Font, pygame.font.Font],
    ):
        self.ms_table = ms_table
        self.theme = theme
        self.cases_config = cases_config
        self.display = display
        # font sizes: (small, medium, large, x-large, xx-large)
        self.fsm, self.fmd, self.flg, self.fxl, self.fxxl = fonts

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def render(
        self,
        screen: pygame.Surface,
        case_page: int,
        w_filter: int,
        cases: list[int],
        page_label_pos: tuple[int, int],
    ) -> None:
        """Draw the full cases view area."""
        th = self.theme
        area = pygame.Rect(
            0, self.display.ui_bar_height,
            screen.get_width(),
            screen.get_height() - self.display.ui_bar_height
            - self.display.status_bar_height,
        )

        # ---- Title ----
        title = self.fxl.render(
            "Таблица 512 конфигураций мульти-типовых MS", True, th.text_color,
        )
        screen.blit(title, (area.x + (area.w - title.get_width()) // 2, area.y + 8))

        # ---- Subtitle ----
        sub = self.fsm.render(
            "case_idx = v0 + v1·4 + v2·16 + v3·64 + w·256   |   "
            "T=4 типа, 4 ребра, 12 точек на ячейку",
            True, th.text_secondary,
        )
        screen.blit(sub, (area.x + (area.w - sub.get_width()) // 2, area.y + 36))

        # ---- Navigation row ----
        pages = max(1, (len(cases) + 15) // 16)
        nav_y = area.y + 48
        nx = area.centerx - 120
        page_lbl = self.fmd.render(
            f"{case_page + 1} / {pages}", True, th.text_color,
        )
        # position after w-filter button: prev(32) + gap(4) + filter(60) + gap(8) = 104
        screen.blit(page_lbl, (nx + 112, nav_y + (32 - page_lbl.get_height()) // 2))

        # ---- Grid of cells ----
        gap = 8          # horizontal gap between cells
        top_y = nav_y + 32
        avail_w = area.w - 40
        avail_h = area.bottom - top_y - 10  # 10px bottom safety margin
        label_lines = 23                        # two text lines below each cell
        row_gap = label_lines + gap             # space for labels + vertical gap
        cell = min(
            165,
            (avail_w - 3 * gap) // 4,
            (avail_h - 3 * row_gap - label_lines) // 4,
        )
        gw = 4 * cell + 3 * gap
        gh = 4 * cell + 3 * row_gap + label_lines
        gx = area.x + (area.w - gw) // 2
        gy = top_y + max(0, (avail_h - gh - label_lines) // 2)

        start = case_page * 16
        for i in range(16):
            ci_abs = start + i
            if ci_abs >= len(cases):
                break
            ci = cases[ci_abs]
            col, row = i % 4, i // 4
            cx = gx + col * (cell + gap)
            cy = gy + row * (cell + row_gap)
            self._draw_cell(screen, cx, cy, cell, ci)

    # ------------------------------------------------------------------
    # Single case cell
    # ------------------------------------------------------------------
    def _draw_cell(
        self,
        screen: pygame.Surface,
        cx: int, cy: int, size: int, case_idx: int,
    ) -> None:
        if case_idx not in self.ms_table:
            return

        rect = pygame.Rect(cx, cy, size, size)
        th = self.theme

        # Decode vertex values and w-flag
        w_val = case_idx // 256
        rem = case_idx % 256
        v3 = rem // 64; rem %= 64
        v2 = rem // 16; rem %= 16
        v1 = rem // 4
        v0 = rem % 4
        vals = [v0, v1, v2, v3]

        # Shadow + background
        pygame.draw.rect(
            screen, (210, 212, 218),
            pygame.Rect(cx + 2, cy + 2, size, size), border_radius=8,
        )
        pygame.draw.rect(screen, th.panel_bg, rect, border_radius=8)
        pygame.draw.rect(screen, th.border, rect, 1, border_radius=8)

        pad = size * 0.18
        inner = pygame.Rect(
            cx + pad, cy + pad, size - 2 * pad, size - 2 * pad,
        )

        # Corner vertex positions
        vtx: list[Point2D] = [
            (inner.left, inner.top),
            (inner.right, inner.top),
            (inner.right, inner.bottom),
            (inner.left, inner.bottom),
        ]

        # Weights for 12-point interpolation (derived from material type)
        weights = [0.1 * (v + 1) for v in vals]
        pts = compute_12_points(0, 0, weights[0], weights[1], weights[2], weights[3])

        def to_px(p: Point2D) -> tuple[int, int]:
            return (int(inner.left + p[0] * inner.width),
                    int(inner.top + p[1] * inner.height))

        # Draw filled triangles for each material block
        blocks = self.ms_table[case_idx]
        fill_colors = self.cases_config.fill_colors
        stroke_colors = self.cases_config.stroke_colors

        for bi in range(4):
            fill_clr = fill_colors[vals[bi]]
            stroke_clr = stroke_colors[vals[bi]]
            block_triangles: tuple = blocks[bi]
            for tri in block_triangles:
                if tri == (0, 0, 0):
                    continue
                pp = [to_px(pts[tri[0]]), to_px(pts[tri[1]]), to_px(pts[tri[2]])]
                try:
                    pygame.draw.polygon(screen, fill_clr, pp)
                    pygame.draw.polygon(screen, stroke_clr, pp, 2)
                except Exception:
                    pass

        # Draw edge intersection points
        used = set()
        for bi in range(4):
            block_triangles = blocks[bi]
            for tri in block_triangles:
                for vi in tri:
                    if vi >= 4 and vi != 0:
                        used.add(vi)

        dot_color = (50, 50, 55)
        for ei in used:
            if 4 <= ei <= 11:
                pygame.draw.circle(screen, dot_color, to_px(pts[ei]), 3)

        # Draw corner vertex circles with labels
        vr = max(8, int(size * 0.08))
        for vi in range(4):
            pos = (int(vtx[vi][0]), int(vtx[vi][1]))
            c = stroke_colors[vals[vi]]
            pygame.draw.circle(screen, c, pos, vr)
            lbl = self.fsm.render(str(vals[vi]), True, (255, 255, 255))
            screen.blit(
                lbl,
                (pos[0] - lbl.get_width() // 2, pos[1] - lbl.get_height() // 2),
            )

        # Labels below the cell
        lbl = self.fsm.render(f"#{case_idx}", True, th.text_color)
        lx = cx + (size - lbl.get_width()) // 2
        ly = cy + size + 2
        screen.blit(lbl, (lx, ly))

        bits = f"{v0}{v1}{v2}{v3} w={w_val}"
        lbl2 = self.fsm.render(bits, True, th.text_secondary)
        screen.blit(lbl2, (cx + (size - lbl2.get_width()) // 2, ly + lbl.get_height()))
