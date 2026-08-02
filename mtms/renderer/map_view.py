"""Map view renderer — terrain map with mesh building, debug overlay, and legend."""
from __future__ import annotations

import pygame
import numpy as np

from mtms.algorithm.table import build_mtms_table
from mtms.algorithm.normalization import normalize_materials
from mtms.algorithm.case_index import compute_case_index, compute_w_flag
from mtms.algorithm.interpolation import compute_12_points
from mtms.algorithm.types import MTMSCase
from mtms.config import ThemeConfig, DisplayConfig, MaterialConfig
from mtms.terrain.materials import MaterialPalette
from mtms.app.camera import Camera


class MapViewRenderer:
    """Handles all rendering for the terrain map view."""

    def __init__(
        self,
        ms_table: dict[int, MTMSCase],
        theme: ThemeConfig,
        materials: MaterialConfig,
        display: DisplayConfig,
        fonts: tuple[pygame.font.Font, pygame.font.Font, pygame.font.Font,
                     pygame.font.Font, pygame.font.Font],
    ):
        self.ms_table = ms_table
        self.theme = theme
        self.materials = materials
        self.display = display
        # font sizes: (small, medium, large, x-large, xx-large)
        self.fsm, self.fmd, self.flg, self.fxl, self.fxxl = fonts

    # ------------------------------------------------------------------
    # Mesh building — pure geometry from heightmap + material map
    # ------------------------------------------------------------------
    def build_mesh(
        self,
        heightmap: np.ndarray,
        mat_map: np.ndarray,
        size: int,
    ) -> list[tuple[list[tuple[float, float, ...]], tuple[int, int, int]]]:
        """Walk the grid and produce (polygon_points, color) tuples.

        Returns a list of (([(x,y),...], (r,g,b)), ...) — one entry per
        triangle in the mesh.
        """
        triangles: list[
            tuple[list[tuple[float, float, ...]], tuple[int, int, int]]
        ] = []

        for y in range(size):
            for x in range(size):
                h0 = heightmap[y][x]
                h1 = heightmap[y][x + 1]
                h2 = heightmap[y + 1][x + 1]
                h3 = heightmap[y + 1][x]

                m0 = int(mat_map[y][x])
                m1 = int(mat_map[y][x + 1])
                m2 = int(mat_map[y + 1][x + 1])
                m3 = int(mat_map[y + 1][x])

                loc = normalize_materials([m0, m1, m2, m3])
                w = compute_w_flag(h0, h1, h2, h3)
                ci = compute_case_index(tuple(loc), w)

                blocks: MTMSCase = self.ms_table[ci]
                pts = compute_12_points(x, y, h0, h1, h2, h3)

                vmats = [m0, m1, m2, m3]
                colors = self.materials.colors

                for bi in range(4):
                    color = colors[vmats[bi]]
                    block_triangles: tuple = blocks[bi]
                    for tri in block_triangles:
                        if tri == (0, 0, 0):
                            continue
                        pp = [pts[tri[0]], pts[tri[1]], pts[tri[2]]]
                        triangles.append((pp, color))

        return triangles

    # ------------------------------------------------------------------
    # Pre-render map to offscreen surface
    # ------------------------------------------------------------------
    def render_map_surface(
        self,
        triangles: list[tuple[list[tuple[float, float, ...]], tuple[int, int, int]]],
        screen: pygame.Surface,
        cell_px: int,
        size: int,
    ) -> pygame.Surface:
        """Draw the complete map (triangles + grid) into a new Surface."""
        sw = size * cell_px + 2
        sh = size * cell_px + 2
        surface = pygame.Surface((sw, sh))
        surface.fill(self.theme.panel_bg)

        for pp, color in triangles:
            sp = [
                (int(p[0] * cell_px) + 1, int(p[1] * cell_px) + 1) for p in pp
            ]
            try:
                pygame.draw.polygon(surface, color, sp)
            except Exception:
                pass

        # Grid lines (only visible at higher zooms)
        if cell_px > 3:
            th = self.theme
            for i in range(size + 1):
                c = i * cell_px + 1
                pygame.draw.line(surface, th.grid_line, (c, 0), (c, sh))
                pygame.draw.line(surface, th.grid_line, (0, c), (sw, c))

        return surface

    # ------------------------------------------------------------------
    # Debug overlay — vertex weights or material names
    # ------------------------------------------------------------------
    def render_debug_overlay(
        self,
        screen: pygame.Surface,
        area: pygame.Rect,
        ox: int, oy: int,
        heightmap: np.ndarray,
        mat_map: np.ndarray,
        cell_px: int,
        size: int,
        debug_mode: int,  # 1=weights, 2=materials
    ) -> None:
        """Overlay vertex labels on the visible viewport area."""
        h = size + 1
        vr = max(3, min(12, cell_px // 3))
        colors = self.materials.colors
        names = self.materials.names

        for y in range(h):
            for x in range(h):
                px = ox + x * cell_px + 1
                py = oy + y * cell_px + 1

                # Skip vertices outside the visible area
                if px < area.left - vr or px > area.right + vr:
                    continue
                if py < area.top - vr or py > area.bottom + vr:
                    continue

                pos = (int(px), int(py))
                midx = int(mat_map[y][x])

                # Background circle for vertex
                pygame.draw.circle(screen, colors[midx], pos, vr + 1)
                pygame.draw.circle(screen, (50, 50, 55), pos, vr + 1, 1)

                if cell_px >= 18:
                    if debug_mode == 1:
                        txt = f"{heightmap[y][x]:.2f}"
                    else:
                        txt = names[midx][:3]
                    ts = self.fsm.render(txt, True, (30, 30, 35))
                    bg = pygame.Surface(
                        (ts.get_width() + 2, ts.get_height() + 2),
                        pygame.SRCALPHA,
                    )
                    bg.fill((255, 255, 255, 185))
                    screen.blit(bg, (pos[0] - ts.get_width() // 2 - 1,
                                     pos[1] - ts.get_height() // 2 - 1))
                    screen.blit(ts, (pos[0] - ts.get_width() // 2,
                                     pos[1] - ts.get_height() // 2))
                else:
                    txt = str(midx) if debug_mode == 2 else f"{int(heightmap[y][x] * 9)}"
                    ts = self.fsm.render(txt, True, (30, 30, 35))
                    screen.blit(ts, (pos[0] - ts.get_width() // 2,
                                     pos[1] - ts.get_height() // 2))

    # ------------------------------------------------------------------
    # Material legend panel (bottom-right of map area)
    # ------------------------------------------------------------------
    def render_legend(self, screen: pygame.Surface, area: pygame.Rect) -> None:
        """Draw the material palette legend in the map view."""
        th = self.theme
        lx = area.right - 160
        ly = area.top + 10
        lw, lh = 150, 148

        s = pygame.Surface((lw, lh), pygame.SRCALPHA)
        s.fill((255, 255, 255, 210))
        screen.blit(s, (lx, ly))
        pygame.draw.rect(screen, th.border, (lx, ly, lw, lh), 1, border_radius=6)

        ts = self.fmd.render("Материалы", True, th.text_color)
        screen.blit(ts, (lx + 8, ly + 6))

        thresholds = self.materials.thresholds
        colors = self.materials.colors
        names = self.materials.names

        for i in range(5):
            iy = ly + 28 + i * 23
            pygame.draw.rect(
                screen, colors[i], (lx + 10, iy, 14, 14), border_radius=2,
            )
            pygame.draw.rect(
                screen, th.border, (lx + 10, iy, 14, 14), 1, border_radius=2,
            )

            if i == 0:
                thr = f"< {thresholds[0]:.2f}"
            elif i < len(thresholds):
                thr = f"{thresholds[i-1]:.2f}-{thresholds[i]:.2f}"
            else:
                thr = f">= {thresholds[-1]:.2f}"

            label = f"{names[i]} ({thr})"
            ts = self.fsm.render(label, True, th.text_color)
            screen.blit(ts, (lx + 30, iy - 1))

    # ------------------------------------------------------------------
    # Main render entry point for the map view
    # ------------------------------------------------------------------
    def render_map_view(
        self,
        screen: pygame.Surface,
        map_surface: pygame.Surface | None,
        camera: Camera,
        debug_mode: int,
        heightmap: np.ndarray | None,
        mat_map: np.ndarray | None,
        cell_px: int,
        size: int,
    ) -> tuple[int, bool]:
        """Draw the map view with all overlays.

        Returns (updated_cell_px, was_dirty) — the cell pixel size and
        whether the surface was regenerated this call.
        """
        area = pygame.Rect(
            0, self.display.ui_bar_height,
            screen.get_width(),
            screen.get_height() - self.display.ui_bar_height
            - self.display.status_bar_height,
        )

        return self._draw_map(
            screen, map_surface, camera, debug_mode,
            heightmap, mat_map, cell_px, size, area,
        )

    def _draw_map(
        self,
        screen: pygame.Surface,
        map_surface: pygame.Surface | None,
        camera: Camera,
        debug_mode: int,
        heightmap: np.ndarray | None,
        mat_map: np.ndarray | None,
        cell_px: int,
        size: int,
        area: pygame.Rect,
    ) -> tuple[int, bool]:
        """Internal drawing routine."""
        screen.set_clip(area)

        sw = map_surface.get_width()
        sh = map_surface.get_height()
        bx = area.x + (area.w - sw) // 2 + int(camera.x)
        by = area.y + (area.h - sh) // 2 + int(camera.y)
        screen.blit(map_surface, (bx, by))

        # Debug overlay
        if debug_mode > 0 and cell_px > 6:
            self.render_debug_overlay(
                screen, area, bx, by, heightmap, mat_map,
                cell_px, size, debug_mode,
            )

        screen.set_clip(None)
        self.render_legend(screen, area)

        return cell_px, False
