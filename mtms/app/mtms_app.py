"""MTMS Viewer Application — thin orchestrator for event loop and rendering.

Delegates all algorithm work to mtms.algorithm, terrain to mtms.terrain,
UI widgets to mtms.ui, and visual rendering to mtms.renderer.
"""
from __future__ import annotations

import random
import sys

import pygame
import numpy as np

from mtms.config import Config, DEFAULT_CONFIG
from mtms.algorithm.table import build_mtms_table
from mtms.algorithm.types import MTMSCase
from mtms.terrain.heightmap import generate_heightmap, classify_height
from mtms.ui import load_fonts, Button, Dropdown
from mtms.renderer.cases_view import CasesViewRenderer
from mtms.renderer.map_view import MapViewRenderer
from mtms.renderer.toolbar import ToolbarRenderer
from mtms.app.camera import Camera


class MTMSApp:
    """Main application — Pygame event loop + state coordination."""

    def __init__(self, cfg: Config | None = None) -> None:
        self.cfg = cfg or DEFAULT_CONFIG
        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.cfg.display.screen_width, self.cfg.display.screen_height),
            pygame.RESIZABLE,
        )
        pygame.display.set_caption("Multi-Type Marching Squares — MTMS Viewer")
        self.clock = pygame.time.Clock()

        fonts = load_fonts()
        self.fsm, self.fmd, self.flg, self.fxl, self.fxxl = fonts

        # ---- State ----
        self.view_mode: int = 0         # 0=cases, 1=map
        self.case_page: int = 0
        self.w_filter: int = -1         # -1=all, 0=w0, 1=w1
        self.debug_mode: int = 0        # 0=off, 1=weights, 2=materials
        self.seed: int = random.randint(0, 999999)
        self.map_size_idx: int = 0
        self.running: bool = True

        self.camera = Camera()

        # ---- Build MTMS lookup table ----
        print("Генерация таблицы 512 кейсов...")
        self.ms_table: dict[int, MTMSCase] = build_mtms_table(
            self.cfg.algorithm.num_types,
        )
        assert len(self.ms_table) == 512, (
            f"Expected 512 cases, got {len(self.ms_table)}"
        )
        print("OK: 512 кейсов.")

        # ---- Terrain ----
        self.heightmap: np.ndarray = np.zeros((2, 2))
        self.mat_map: np.ndarray = np.zeros_like(self.heightmap, dtype=int)
        self._generate_terrain()

        # ---- Map cache ----
        self.map_dirty: bool = True
        self.map_surface: pygame.Surface | None = None
        self.triangles: list = []
        self.cell_px: int = 1

        # ---- UI widgets ----
        self._create_ui()

        # ---- Renderers ----
        self.cases_renderer = CasesViewRenderer(
            self.ms_table, self.cfg.theme, self.cfg.cases,
            self.cfg.display, fonts,
        )
        self.map_renderer = MapViewRenderer(
            self.ms_table, self.cfg.theme, self.cfg.materials,
            self.cfg.display, fonts,
        )
        self.toolbar_renderer = ToolbarRenderer(self.cfg.theme, self.cfg.display)

    # ------------------------------------------------------------------
    # Terrain generation
    # ------------------------------------------------------------------
    def _generate_terrain(self) -> None:
        size = self.cfg.algorithm.map_sizes[self.map_size_idx]
        self.heightmap = generate_heightmap(size, seed=self.seed)
        thresholds = self.cfg.materials.thresholds
        self.mat_map = np.zeros_like(self.heightmap, dtype=int)

        for y in range(self.heightmap.shape[0]):
            for x in range(self.heightmap.shape[1]):
                self.mat_map[y][x] = classify_height(
                    self.heightmap[y][x], thresholds,
                )

        self.camera.reset()
        self.map_dirty = True

    # ------------------------------------------------------------------
    # UI creation
    # ------------------------------------------------------------------
    def _create_ui(self) -> None:
        th = self.cfg.theme
        x0, y0, g = 10, 8, 6
        bw, bh = 95, 34

        self.btn_cases = Button(
            (x0, y0, bw, bh), "Кейсы", self.fmd, toggle=True, theme=th,
        )
        self.btn_cases.active = True

        self.btn_map = Button(
            (x0 + bw + g, y0, bw, bh), "Карта", self.fmd, toggle=True, theme=th,
        )

        map_options = [
            f"{s}x{s}" for s in self.cfg.algorithm.map_sizes
        ]
        self.dd_size = Dropdown(
            (x0 + 2 * (bw + g) + 50, y0, 78, bh),
            map_options, self.fmd, selected=0, theme=th,
        )

        self.btn_debug = Button(
            (x0 + 2 * (bw + g) + 140, y0, 130, bh),
            "Отладка", self.fmd, toggle=True, theme=th,
        )

        self.btn_regen = Button(
            (x0 + 2 * (bw + g) + 280, y0, 115, bh),
            "Новая карта", self.fmd, theme=th,
        )

        # Cases view navigation buttons
        self.btn_prev = Button((0, 0, 32, 32), "<", self.fmd, theme=th)
        self.btn_next = Button((0, 0, 32, 32), ">", self.fmd, theme=th)
        self.btn_wfilter = Button(
            (0, 0, 60, 32), "Все", self.fmd, toggle=True, theme=th,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_cases_list(self) -> list[int]:
        """Return filtered case indices based on w_filter."""
        if self.w_filter < 0:
            return list(range(512))
        start = self.w_filter * 256
        return list(range(start, start + 256))

    def _ensure_map_rendered(self) -> None:
        """Build mesh and pre-render map surface if dirty."""
        if not self.map_dirty:
            return

        size = self.cfg.algorithm.map_sizes[self.map_size_idx]

        # Build triangle mesh
        self.triangles = self.map_renderer.build_mesh(
            self.heightmap, self.mat_map, size,
        )

        # Compute cell pixel size
        base = min(self.screen.get_width(),
                   self.screen.get_height() - self.cfg.display.ui_bar_height
                   - self.cfg.display.status_bar_height) / (size + 2)
        self.cell_px = max(2, int(base * self.camera.zoom))

        # Render to offscreen surface
        self.map_surface = self.map_renderer.render_map_surface(
            self.triangles, self.screen, self.cell_px, size,
        )
        self.map_dirty = False

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def handle_events(self) -> None:
        """Process all pending pygame events."""
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
                return

            if ev.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(ev.size, pygame.RESIZABLE)
                self.map_dirty = True

            # Handle toolbar widgets
            self.btn_cases.handle(ev)
            self.btn_map.handle(ev)
            self.dd_size.handle(ev)
            self.btn_debug.handle(ev)
            self.btn_regen.handle(ev)

            if self.view_mode == 0:
                self.btn_prev.handle(ev)
                self.btn_next.handle(ev)
                self.btn_wfilter.handle(ev)

            # ---- Tab switching ----
            if self.btn_cases.clicked:
                self.view_mode = 0
                self.btn_cases.active = True
                self.btn_map.active = False
            if self.btn_map.clicked:
                self.view_mode = 1
                self.btn_map.active = True
                self.btn_cases.active = False

            # ---- Debug toggle ----
            if self.btn_debug.clicked:
                self.debug_mode = (self.debug_mode + 1) % 3
                labels = ["Отладка", "Отладка: веса", "Отладка: матер."]
                self.btn_debug.text = labels[self.debug_mode]
                self.btn_debug.active = self.debug_mode > 0

            # ---- Regenerate terrain ----
            if self.btn_regen.clicked:
                self.seed = random.randint(0, 999999)
                self._generate_terrain()

            # ---- Size dropdown change ----
            if self.dd_size.changed:
                self.map_size_idx = self.dd_size.sel
                self._generate_terrain()

            # ---- Cases navigation ----
            cases = self._get_cases_list()
            pages = max(1, (len(cases) + 15) // 16)
            self.case_page = max(0, min(self.case_page, pages - 1))

            if self.view_mode == 0:
                if self.btn_prev.clicked:
                    self.case_page = max(0, self.case_page - 1)
                if self.btn_next.clicked:
                    self.case_page = min(pages - 1, self.case_page + 1)
                if self.btn_wfilter.clicked:
                    cycle = {-1: 0, 0: 1, 1: -1}
                    self.w_filter = cycle[self.w_filter]
                    labels = {-1: "Все", 0: "w=0", 1: "w=1"}
                    self.btn_wfilter.text = labels[self.w_filter]
                    self.btn_wfilter.active = self.w_filter >= 0
                    self.case_page = 0

            # ---- Zoom (map view) ----
            if ev.type == pygame.MOUSEWHEEL and self.view_mode == 1:
                factor = 1.15 if ev.y > 0 else 1.0 / 1.15
                self.camera.update_zoom(factor)
                self.map_dirty = True

            # ---- Pan (map view) ----
            if self.view_mode == 1:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (2, 3):
                    self._pan_start = ev.pos
                    self._pan_cam0 = (self.camera.x, self.camera.y)
                if (ev.type == pygame.MOUSEMOTION
                        and hasattr(self, '_pan_start')):
                    if self._pan_start is not None:
                        dx = ev.pos[0] - self._pan_start[0]
                        dy = ev.pos[1] - self._pan_start[1]
                        self.camera.set_pan(
                            self._pan_cam0[0] + dx,
                            self._pan_cam0[1] + dy,
                        )
                if (ev.type == pygame.MOUSEBUTTONUP
                        and ev.button in (2, 3)
                        and hasattr(self, '_pan_start')):
                    self._pan_start = None

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def _position_nav_buttons(self) -> None:
        """Set nav button rects to match the cases_view layout."""
        area_y = self.cfg.display.ui_bar_height
        nav_y = area_y + 48
        nx = self.screen.get_width() // 2 - 120
        self.btn_prev.rect.topleft = (nx, nav_y)
        self.btn_wfilter.rect.topleft = (nx + 44, nav_y)
        self.btn_next.rect.topleft = (nx + 140, nav_y)

    def draw(self) -> None:
        """Full frame render."""
        self.screen.fill(self.cfg.theme.bg_color)

        if self.view_mode == 0:
            cases = self._get_cases_list()
            self.cases_renderer.render(
                self.screen, self.case_page, self.w_filter, cases,
                page_label_pos=(0, 0),
            )
            self._position_nav_buttons()
            nav_buttons = [self.btn_prev, self.btn_next, self.btn_wfilter]
        else:
            self._ensure_map_rendered()
            self.map_renderer.render_map_view(
                self.screen, self.map_surface, self.camera,
                self.debug_mode, self.heightmap, self.mat_map,
                self.cell_px,
                self.cfg.algorithm.map_sizes[self.map_size_idx],
            )
            nav_buttons = []

        # Toolbar + status
        toolbar_buttons = [
            self.btn_cases, self.btn_map, self.dd_size,
            self.btn_debug, self.btn_regen,
        ]
        self.toolbar_renderer.render_toolbar(
            self.screen, toolbar_buttons, nav_buttons if nav_buttons else None,
        )

        # Status bar message
        if self.view_mode == 0:
            cases = self._get_cases_list()
            pages = max(1, (len(cases) + 15) // 16)
            filter_label = ["Все", "w=0", "w=1"][max(0, self.w_filter)]
            msg = (f"Мульти-типовые MS — 512 кейсов | "
                   f"Страница {self.case_page+1}/{pages} | Фильтр: {filter_label}")
        else:
            sz = self.cfg.algorithm.map_sizes[self.map_size_idx]
            dbg = ["Выкл", "Веса вершин", "Номера материалов"][self.debug_mode]
            msg = (f"Карта {sz}x{sz} | Seed: {self.seed} | "
                   f"Зум: {self.camera.zoom:.1f}x | Отладка: {dbg} | "
                   f"ПКМ/СКМ: панорама")

        self.toolbar_renderer.render_status(self.screen, msg, self.fsm)

        pygame.display.flip()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Start the Pygame event/render loop."""
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(self.cfg.display.fps)
        pygame.quit()
        sys.exit(0)
