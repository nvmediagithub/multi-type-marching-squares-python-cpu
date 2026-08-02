#!/usr/bin/env python3
"""
Multi-Type Marching Squares Visualizer
=======================================
Функциональность:
  - Таблица 512 кейсов: T=4 типа, 4^4 комбинаций × 2 (флаг w)
  - Нормализация идентификаторов материалов (последовательная модульная арифметика)
  - 12 точек интерполяции на ячейку (4 вершины + 4 ребра + 4 диагонали)
  - Визуализация кейсов: постранично по 16 (4×4) с навигацией
  - Генерация карты: Perlin noise, 5 материалов (Вода/Песок/Трава/Скалы/Снег)
  - Отладка: веса вершин и номера материалов
  - Зум (колесо) и панорамирование (ПКМ/СКМ)
  - Светлая тема
"""

import pygame
import numpy as np
import math
import sys
import random
import os
import traceback

# ================================================================
# CONSTANTS
# ================================================================
SCREEN_W, SCREEN_H = 1280, 800
FPS = 60
UI_BAR_H = 50
STATUS_H = 26

T = 4  # Количество типов материалов в таблице

# ---- Light Theme ----
BG = (240, 241, 245)
PANEL_BG = (255, 255, 255)
TEXT_CLR = (35, 35, 40)
TEXT_SEC = (120, 122, 130)
ACCENT = (65, 125, 215)
ACCENT_TEXT = (255, 255, 255)
BTN_CLR = (225, 228, 235)
BTN_HOVER = (210, 215, 225)
BORDER = (208, 210, 218)
GRID_LINE = (222, 224, 232)

# ---- Terrain Materials (5 global types) ----
MAT_COLORS = [
    (70, 150, 220),   # 0: Вода (голубой)
    (215, 195, 105),  # 1: Песок (жёлтый)
    (95, 185, 95),    # 2: Трава (зелёный)
    (145, 143, 143),  # 3: Скалы (серый)
    (235, 235, 242),  # 4: Снег (белый)
]
MAT_NAMES = ["Вода", "Песок", "Трава", "Скалы", "Снег"]
THRESHOLDS = [0.25, 0.40, 0.65, 0.85]

# ---- Abstract colors for cases view (types 0..3) ----
CASE_COLORS = [
    (55, 120, 200),   # 0: Blue
    (50, 165, 50),    # 1: Green
    (200, 140, 40),   # 2: Orange
    (160, 55, 160),   # 3: Purple
]
CASE_FILL = [
    (190, 218, 245),
    (195, 238, 195),
    (248, 228, 185),
    (230, 200, 230),
]

MAP_SIZES = [16, 32, 64, 128]

# ================================================================
# FONT LOADING
# ================================================================
def load_fonts():
    file_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for p in file_paths:
        if os.path.exists(p):
            try:
                return (pygame.font.Font(p, 12), pygame.font.Font(p, 14),
                        pygame.font.Font(p, 17), pygame.font.Font(p, 21),
                        pygame.font.Font(p, 26))
            except Exception:
                pass
    for name in ['DejaVu Sans', 'Liberation Sans', 'FreeSans', 'Arial']:
        try:
            f = pygame.font.SysFont(name, 14)
            if f.render("Тест", True, (0, 0, 0)).get_width() > 10:
                return (pygame.font.SysFont(name, 12), pygame.font.SysFont(name, 14),
                        pygame.font.SysFont(name, 17), pygame.font.SysFont(name, 21),
                        pygame.font.SysFont(name, 26))
        except Exception:
            pass
    return (pygame.font.Font(None, 15), pygame.font.Font(None, 17),
            pygame.font.Font(None, 20), pygame.font.Font(None, 24),
            pygame.font.Font(None, 28))


# ================================================================
# MULTI-TYPE TABLE GENERATION
# Ported from world_settings.gd -> _build_multitype_table()
#
# Structure: table[case_idx] = [block0, block1, block2, block3]
#   block_i = [tri0, tri1, tri2]
#   tri = [vertex_a, vertex_b, vertex_c]
#
# Vertex indices 0..11:
#   0-3:  corners (v0=top-left, v1=top-right, v2=bot-right, v3=bot-left)
#   4-7:  edge midpoints (4=top, 5=right, 6=bottom, 7=left)
#   8-11: diagonal interpolation (8=v0->center, 9=v1->center, 10=v2->center, 11=v3->center)
#
# case_idx = v0 + v1*T + v2*T^2 + v3*T^3 + w*T^4
#          = v0 + 4*v1 + 16*v2 + 64*v3 + 256*w
# ================================================================
def build_mtms_table():
    T = 4
    cases_per_w = T ** 4  # 256

    table = {}
    Z = [0, 0, 0]

    for w in range(2):
        for v0 in range(T):
            for v1 in range(T):
                for v2 in range(T):
                    for v3 in range(T):
                        vals = [v0, v1, v2, v3]
                        ci = v0 + v1 * T + v2 * T * T + v3 * T * T * T + w * cases_per_w
                        b = [[list(Z), list(Z), list(Z)] for _ in range(4)]
                        uq = len(set(vals))

                        if uq == 1:
                            b[0] = [[0, 1, 3], [3, 1, 2], list(Z)]

                        elif uq == 2 and vals[0] != vals[2] and vals[1] != vals[3]:
                            if vals[0] == vals[1]:
                                b[0] = [[0, 1, 5], [0, 5, 7], list(Z)]
                                b[2] = [[2, 3, 7], [2, 7, 5], list(Z)]
                            else:
                                b[1] = [[1, 2, 6], [1, 6, 4], list(Z)]
                                b[3] = [[3, 0, 4], [3, 4, 6], list(Z)]

                        elif vals[0] == vals[1] and vals[1] == vals[2]:
                            if w == 0:
                                b[1] = [[0, 1, 7], [7, 1, 6], [6, 1, 2]]
                                b[3] = [[3, 7, 6], list(Z), list(Z)]
                            else:
                                b[0] = [[0, 11, 7], [0, 1, 11], list(Z)]
                                b[2] = [[2, 6, 11], [2, 11, 1], list(Z)]
                                b[3] = [[6, 3, 11], [11, 3, 7], list(Z)]

                        elif vals[3] == vals[1] and vals[1] == vals[2]:
                            if w == 0:
                                b[0] = [[0, 8, 7], [0, 4, 8], list(Z)]
                                b[1] = [[1, 8, 4], [1, 2, 8], list(Z)]
                                b[3] = [[3, 7, 8], [3, 8, 2], list(Z)]
                            else:
                                b[0] = [[0, 4, 7], list(Z), list(Z)]
                                b[2] = [[2, 3, 7], [2, 7, 4], [2, 4, 1]]

                        elif vals[3] == vals[0] and vals[0] == vals[2]:
                            if w == 0:
                                b[1] = [[1, 5, 4], list(Z), list(Z)]
                                b[3] = [[3, 0, 4], [3, 4, 5], [3, 5, 2]]
                            else:
                                b[0] = [[0, 4, 9], [0, 9, 3], list(Z)]
                                b[1] = [[1, 5, 9], [1, 9, 4], list(Z)]
                                b[2] = [[2, 9, 5], [2, 3, 9], list(Z)]

                        elif vals[3] == vals[0] and vals[0] == vals[1]:
                            if w == 0:
                                b[0] = [[0, 1, 5], [0, 5, 6], [0, 6, 3]]
                                b[2] = [[2, 6, 5], list(Z), list(Z)]
                            else:
                                b[1] = [[1, 5, 10], [1, 10, 0], list(Z)]
                                b[2] = [[2, 6, 10], [2, 10, 5], list(Z)]
                                b[3] = [[3, 10, 6], [3, 0, 10], list(Z)]

                        else:
                            if w == 0:
                                b[0] = [[7, 0, 8], [8, 0, 4], list(Z)]
                                b[1] = [[4, 1, 8], [8, 1, 10], [10, 1, 5]]
                                b[2] = [[5, 2, 10], [10, 2, 6], list(Z)]
                                b[3] = [[6, 3, 10], [10, 3, 8], [8, 3, 7]]
                            else:
                                b[0] = [[4, 9, 0], [0, 9, 11], [0, 11, 7]]
                                b[1] = [[4, 1, 9], [9, 1, 5], list(Z)]
                                b[2] = [[5, 2, 9], [9, 2, 11], [2, 6, 11]]
                                b[3] = [[6, 3, 11], [11, 3, 7], list(Z)]

                        table[ci] = b
    return table


# ================================================================
# MATERIAL NORMALIZATION (from mc_3d_build.glsl)
# Последовательная модульная арифметика для приведения
# глобальных идентификаторов к локальным 0..3
# ================================================================
def normalize_materials(global_ids):
    nums = [g + 1 for g in global_ids]
    for _ in range(4):
        mx = max(nums)
        if mx <= 0:
            break
        nums = [n % mx + 1 for n in nums]
    mx = max(nums)
    if mx > 0:
        nums = [n % mx for n in nums]
    return nums


# ================================================================
# W FLAG — разрешение диагональной неоднозначности (from GLSL)
# w = round(w_ac / (w_ac + w_bd))
# w_ac = wa + wc,  w_bd = wb + wd
# ================================================================
def compute_w_flag(wa, wb, wc, wd):
    w_ac = wa + wc
    w_bd = wb + wd
    s = w_ac + w_bd
    if abs(s) < 1e-12:
        return 0
    return int(w_ac / s + 0.5)


# ================================================================
# 12 INTERPOLATION POINTS (from mc_3d_build.glsl)
# pts[0..3]  = угловые вершины ячейки
# pts[4..7]  = точки пересечения контуров с рёбрами
# pts[8..11] = диагональные интерполяционные точки
# ================================================================
def compute_12_points(cx, cy, wa, wb, wc, wd):
    """cx, cy — целочисленные координаты ячейки в сетке."""
    pts = [None] * 12
    pts[0] = (float(cx),     float(cy))      # v0: top-left
    pts[1] = (float(cx + 1), float(cy))      # v1: top-right
    pts[2] = (float(cx + 1), float(cy + 1))  # v2: bot-right
    pts[3] = (float(cx),     float(cy + 1))  # v3: bot-left

    ctr = (cx + 0.5, cy + 0.5)

    def lerp2(a, b, t):
        return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))

    def elerp(a, b, va, vb):
        s = va + vb
        t = vb / s if abs(s) > 1e-12 else 0.5
        return lerp2(a, b, t)

    pts[4] = elerp(pts[0], pts[1], wa, wb)   # top edge
    pts[5] = elerp(pts[1], pts[2], wb, wc)   # right edge
    pts[6] = elerp(pts[2], pts[3], wc, wd)   # bottom edge
    pts[7] = elerp(pts[3], pts[0], wd, wa)   # left edge

    w_ac = wa + wc
    w_bd = wb + wd
    s = w_ac + w_bd
    t_bd = w_bd / s if abs(s) > 1e-12 else 0.5
    t_ac = w_ac / s if abs(s) > 1e-12 else 0.5

    pts[8]  = lerp2(pts[0], ctr, t_bd)       # v0 -> center, weight w_bd
    pts[9]  = lerp2(pts[1], ctr, t_ac)       # v1 -> center, weight w_ac
    pts[10] = lerp2(pts[2], ctr, t_bd)       # v2 -> center, weight w_bd
    pts[11] = lerp2(pts[3], ctr, t_ac)       # v3 -> center, weight w_ac

    return pts


# ================================================================
# PERLIN NOISE (чистый numpy, без внешних зависимостей)
# ================================================================
def _perlin_noise_2d(shape, seed=42, scale=1.0):
    """Векторизованный 2D Perlin noise на numpy.
    Возвращает массив shape со значениями примерно в [-1, 1].
    """
    rng = np.random.RandomState(seed)
    h, w = shape
    # Градиентные векторы для узлов решётки
    gx = rng.randn(h + 2, w + 2)
    gy = rng.randn(h + 2, w + 2)
    # Координаты вершин в пространстве шума
    xs = np.arange(w, dtype=np.float64) * scale
    ys = np.arange(h, dtype=np.float64) * scale
    xx, yy = np.meshgrid(xs, ys)
    # Целые части (узлы решётки)
    xi = np.floor(xx).astype(int)
    yi = np.floor(yy).astype(int)
    # Дробные части
    xf = xx - xi
    yf = yy - yi
    # Fade-функция (5t^3 - 3t^4)^2  (improved Perlin)
    u = xf * xf * xf * (xf * (xf * 6.0 - 15.0) + 10.0)
    v = yf * yf * yf * (yf * (yf * 6.0 - 15.0) + 10.0)
    # Гарантируем, что индексы в пределах [0, h+1] x [0, w+1]
    xi = np.clip(xi, 0, h)
    yi = np.clip(yi, 0, w)
    # Скалярные произведения градиентов и векторов смещения
    def dot(gx_arr, gy_arr, dx, dy):
        return gx_arr * dx + gy_arr * dy
    n00 = dot(gx[yi, xi],     gy[yi, xi],     xf,      yf)
    n10 = dot(gx[yi, xi + 1], gy[yi, xi + 1], xf - 1.0, yf)
    n01 = dot(gx[yi + 1, xi], gy[yi + 1, xi], xf,      yf - 1.0)
    n11 = dot(gx[yi + 1, xi + 1], gy[yi + 1, xi + 1], xf - 1.0, yf - 1.0)
    # Билинейная интерполяция с fade
    nx0 = n00 + u * (n10 - n00)
    nx1 = n01 + u * (n11 - n01)
    return nx0 + v * (nx1 - nx0)


def generate_heightmap(size, seed=42, scale=0.08, octaves=4, persistence=0.5):
    """Генерация карты высот на основе Perlin noise.
    Возвращает numpy-массив (size+1)x(size+1) со значениями в [0, 1].
    """
    h = size + 1
    hm = np.zeros((h, h), dtype=np.float64)
    amp = 1.0
    freq = 1.0
    for layer in range(octaves):
        hm += amp * _perlin_noise_2d((h, h), seed=seed + layer * 1000, scale=scale * freq)
        amp *= persistence
        freq *= 2.0
    mn, mx = hm.min(), hm.max()
    if mx - mn > 1e-9:
        hm = (hm - mn) / (mx - mn)
    return hm


def classify_height(h):
    for i, t in enumerate(THRESHOLDS):
        if h < t:
            return i
    return len(THRESHOLDS)


# ================================================================
# UI WIDGETS
# ================================================================
class Button:
    def __init__(self, rect, text, font, toggle=False):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.toggle = toggle
        self.active = False
        self.hovered = False
        self.clicked = False

    def handle(self, ev):
        self.clicked = False
        if ev.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(ev.pos)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos):
                self.clicked = True
                if self.toggle:
                    self.active = not self.active

    def draw(self, surf):
        if self.toggle and self.active:
            clr, tc = ACCENT, ACCENT_TEXT
        elif self.hovered:
            clr, tc = BTN_HOVER, TEXT_CLR
        else:
            clr, tc = BTN_CLR, TEXT_CLR
        pygame.draw.rect(surf, clr, self.rect, border_radius=6)
        pygame.draw.rect(surf, BORDER, self.rect, 1, border_radius=6)
        ts = self.font.render(self.text, True, tc)
        surf.blit(ts, (self.rect.x + (self.rect.w - ts.get_width()) // 2,
                        self.rect.y + (self.rect.h - ts.get_height()) // 2))


class Dropdown:
    def __init__(self, rect, options, font, sel=0):
        self.rect = pygame.Rect(rect)
        self.options = options
        self.font = font
        self.sel = sel
        self.open = False
        self.changed = False

    def handle(self, ev):
        self.changed = False
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.open:
                for i in range(len(self.options)):
                    r = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.h,
                                    self.rect.w, self.rect.h)
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

    def draw(self, surf):
        pygame.draw.rect(surf, BTN_CLR, self.rect, border_radius=6)
        pygame.draw.rect(surf, BORDER, self.rect, 1, border_radius=6)
        ts = self.font.render(str(self.options[self.sel]), True, TEXT_CLR)
        surf.blit(ts, (self.rect.x + 8,
                        self.rect.y + (self.rect.h - ts.get_height()) // 2))
        ax = self.rect.right - 16
        ay = self.rect.centery
        pygame.draw.polygon(surf, TEXT_SEC,
                            [(ax - 3, ay - 2), (ax + 3, ay - 2), (ax, ay + 3)])
        if self.open:
            for i, opt in enumerate(self.options):
                r = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.h,
                                self.rect.w, self.rect.h)
                c = BTN_HOVER if r.collidepoint(pygame.mouse.get_pos()) else PANEL_BG
                pygame.draw.rect(surf, c, r)
                pygame.draw.rect(surf, BORDER, r, 1)
                ts = self.font.render(str(opt), True, TEXT_CLR)
                surf.blit(ts, (r.x + 8, r.y + (r.h - ts.get_height()) // 2))


# ================================================================
# MAIN APPLICATION
# ================================================================
class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
        pygame.display.set_caption("Multi-Type Marching Squares — MTMS Viewer")
        self.clock = pygame.time.Clock()

        self.fsm, self.fmd, self.flg, self.fxl, self.fxxl = load_fonts()

        # ---- State ----
        self.view = 0            # 0=cases, 1=map
        self.case_page = 0
        self.w_filter = -1       # -1=all, 0=w0, 1=w1
        self.debug_mode = 0      # 0=off, 1=weights, 2=materials
        self.seed = random.randint(0, 999999)
        self.map_size_idx = 0
        self.running = True

        # Camera
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.zoom = 1.0
        self.panning = False
        self.pan_start = None
        self.pan_cam0 = None

        # ---- Build MTMS table ----
        print("Генерация таблицы 512 кейсов...")
        self.ms_table = build_mtms_table()
        assert len(self.ms_table) == 512, f"Expected 512 cases, got {len(self.ms_table)}"
        print("OK: 512 кейсов.")

        # ---- Terrain ----
        print("Генерация карты...")
        self._generate_terrain()
        print("OK.")

        # ---- Map cache ----
        self.map_dirty = True
        self.map_surface = None
        self.triangles = []   # list of ([(x,y),(x,y),(x,y)], (r,g,b))

        # ---- UI ----
        self._create_ui()

    # -------------------------------------------------------
    # Terrain generation
    # -------------------------------------------------------
    def _generate_terrain(self):
        size = MAP_SIZES[self.map_size_idx]
        self.heightmap = generate_heightmap(size, seed=self.seed)
        self.mat_map = np.zeros_like(self.heightmap, dtype=int)
        for y in range(self.heightmap.shape[0]):
            for x in range(self.heightmap.shape[1]):
                self.mat_map[y][x] = classify_height(self.heightmap[y][x])
        self.cam_x = self.cam_y = 0.0
        self.zoom = 1.0
        self.map_dirty = True

    # -------------------------------------------------------
    # Build mesh triangles for map view
    # -------------------------------------------------------
    def _build_mesh(self):
        size = MAP_SIZES[self.map_size_idx]
        self.triangles = []
        for y in range(size):
            for x in range(size):
                h0 = self.heightmap[y][x]
                h1 = self.heightmap[y][x + 1]
                h2 = self.heightmap[y + 1][x + 1]
                h3 = self.heightmap[y + 1][x]
                m0 = self.mat_map[y][x]
                m1 = self.mat_map[y][x + 1]
                m2 = self.mat_map[y + 1][x + 1]
                m3 = self.mat_map[y + 1][x]

                loc = normalize_materials([m0, m1, m2, m3])
                w = compute_w_flag(h0, h1, h2, h3)
                ci = loc[0] + loc[1] * 4 + loc[2] * 16 + loc[3] * 64 + w * 256
                blocks = self.ms_table[ci]
                pts = compute_12_points(x, y, h0, h1, h2, h3)

                vmats = [m0, m1, m2, m3]
                for bi in range(4):
                    color = MAT_COLORS[vmats[bi]]
                    for tri in blocks[bi]:
                        if tri == [0, 0, 0]:
                            continue
                        pp = [pts[tri[0]], pts[tri[1]], pts[tri[2]]]
                        self.triangles.append((pp, color))

    # -------------------------------------------------------
    # Pre-render map surface
    # -------------------------------------------------------
    def _render_map_surface(self):
        size = MAP_SIZES[self.map_size_idx]
        self._build_mesh()
        base = min(self.screen.get_width(), self.screen.get_height() - UI_BAR_H - STATUS_H) / (size + 2)
        cell = max(2, int(base * self.zoom))
        sw = size * cell + 2
        sh = size * cell + 2
        self.map_surface = pygame.Surface((sw, sh))
        self.map_surface.fill(PANEL_BG)
        for pp, color in self.triangles:
            sp = [(int(p[0] * cell) + 1, int(p[1] * cell) + 1) for p in pp]
            try:
                pygame.draw.polygon(self.map_surface, color, sp)
            except Exception:
                pass
        # Grid
        if cell > 3:
            for i in range(size + 1):
                c = i * cell + 1
                pygame.draw.line(self.map_surface, GRID_LINE, (c, 0), (c, sh))
                pygame.draw.line(self.map_surface, GRID_LINE, (0, c), (sw, c))
        self.cell_px = cell
        self.map_dirty = False

    # -------------------------------------------------------
    # UI creation
    # -------------------------------------------------------
    def _create_ui(self):
        x0, y0, g = 10, 8, 6
        bw, bh = 95, 34
        self.btn_cases = Button((x0, y0, bw, bh), "Кейсы", self.fmd, toggle=True)
        self.btn_cases.active = True
        self.btn_map = Button((x0 + bw + g, y0, bw, bh), "Карта", self.fmd, toggle=True)

        self.dd_size = Dropdown((x0 + 2 * (bw + g) + 50, y0, 78, bh),
                                [f"{s}x{s}" for s in MAP_SIZES], self.fmd, 0)

        self.btn_debug = Button((x0 + 2 * (bw + g) + 140, y0, 130, bh),
                                "Отладка", self.fmd, toggle=True)
        self.btn_regen = Button((x0 + 2 * (bw + g) + 280, y0, 115, bh),
                                "Новая карта", self.fmd)
        # Cases view navigation
        self.btn_prev = Button((0, 0, 32, 32), "<", self.fmd)
        self.btn_next = Button((0, 0, 32, 32), ">", self.fmd)
        self.btn_wfilter = Button((0, 0, 60, 32), "Все", self.fmd, toggle=True)

    # -------------------------------------------------------
    # Event handling
    # -------------------------------------------------------
    def _get_cases_list(self):
        """Return list of case indices based on w_filter."""
        if self.w_filter < 0:
            return list(range(512))
        return list(range(self.w_filter * 256, self.w_filter * 256 + 256))

    def handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
                return
            if ev.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(ev.size, pygame.RESIZABLE)
                self.map_dirty = True

            self.btn_cases.handle(ev)
            self.btn_map.handle(ev)
            self.dd_size.handle(ev)
            self.btn_debug.handle(ev)
            self.btn_regen.handle(ev)

            if self.view == 0:
                self.btn_prev.handle(ev)
                self.btn_next.handle(ev)
                self.btn_wfilter.handle(ev)

            # ---- Tab switching ----
            if self.btn_cases.clicked:
                self.view = 0
                self.btn_cases.active = True
                self.btn_map.active = False
            if self.btn_map.clicked:
                self.view = 1
                self.btn_map.active = True
                self.btn_cases.active = False

            # ---- Debug ----
            if self.btn_debug.clicked:
                self.debug_mode = (self.debug_mode + 1) % 3
                self.btn_debug.text = ["Отладка", "Отладка: веса", "Отладка: матер."][self.debug_mode]
                self.btn_debug.active = self.debug_mode > 0

            # ---- Regenerate ----
            if self.btn_regen.clicked:
                self.seed = random.randint(0, 999999)
                self._generate_terrain()

            # ---- Size change ----
            if self.dd_size.changed:
                self.map_size_idx = self.dd_size.sel
                self._generate_terrain()

            # ---- Cases navigation ----
            cases = self._get_cases_list()
            pages = max(1, (len(cases) + 15) // 16)
            self.case_page = max(0, min(self.case_page, pages - 1))

            if self.view == 0:
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
            if ev.type == pygame.MOUSEWHEEL and self.view == 1:
                factor = 1.15 if ev.y > 0 else 1.0 / 1.15
                self.zoom = max(0.2, min(25.0, self.zoom * factor))
                self.map_dirty = True

            # ---- Pan ----
            if self.view == 1:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (2, 3):
                    self.panning = True
                    self.pan_start = ev.pos
                    self.pan_cam0 = (self.cam_x, self.cam_y)
                if ev.type == pygame.MOUSEMOTION and self.panning:
                    dx = ev.pos[0] - self.pan_start[0]
                    dy = ev.pos[1] - self.pan_start[1]
                    self.cam_x = self.pan_cam0[0] + dx
                    self.cam_y = self.pan_cam0[1] + dy
                if ev.type == pygame.MOUSEBUTTONUP and ev.button in (2, 3):
                    self.panning = False

    # -------------------------------------------------------
    # Drawing
    # -------------------------------------------------------
    def draw(self):
        self.screen.fill(BG)
        if self.view == 0:
            self._draw_cases_view()
        else:
            self._draw_map_view()
        self._draw_toolbar()
        self._draw_status()
        pygame.display.flip()

    def _draw_toolbar(self):
        bar = pygame.Rect(0, 0, self.screen.get_width(), UI_BAR_H)
        pygame.draw.rect(self.screen, PANEL_BG, bar)
        pygame.draw.line(self.screen, BORDER, (0, UI_BAR_H), (self.screen.get_width(), UI_BAR_H))
        self.btn_cases.draw(self.screen)
        self.btn_map.draw(self.screen)
        self.dd_size.draw(self.screen)
        self.btn_debug.draw(self.screen)
        self.btn_regen.draw(self.screen)
        if self.view == 0:
            self.btn_prev.draw(self.screen)
            self.btn_next.draw(self.screen)
            self.btn_wfilter.draw(self.screen)

    def _draw_status(self):
        y = self.screen.get_height() - STATUS_H
        sw = self.screen.get_width()
        pygame.draw.rect(self.screen, PANEL_BG, (0, y, sw, STATUS_H))
        pygame.draw.line(self.screen, BORDER, (0, y), (sw, y))
        if self.view == 0:
            cases = self._get_cases_list()
            pages = max(1, (len(cases) + 15) // 16)
            msg = f"Мульти-типовые MS — 512 кейсов | Страница {self.case_page+1}/{pages} | Фильтр: {['Все','w=0','w=1'][self.w_filter]}"
        else:
            sz = MAP_SIZES[self.map_size_idx]
            dbg = ["Выкл", "Веса вершин", "Номера материалов"][self.debug_mode]
            msg = f"Карта {sz}x{sz} | Seed: {self.seed} | Зум: {self.zoom:.1f}x | Отладка: {dbg} | ПКМ/СКМ: панорама"
        ts = self.fsm.render(msg, True, TEXT_SEC)
        self.screen.blit(ts, (12, y + (STATUS_H - ts.get_height()) // 2))

    # ========== CASES VIEW ==========
    def _draw_cases_view(self):
        area = pygame.Rect(0, UI_BAR_H, self.screen.get_width(),
                           self.screen.get_height() - UI_BAR_H - STATUS_H)

        # Title
        title = self.fxl.render("Таблица 512 конфигураций мульти-типовых MS", True, TEXT_CLR)
        self.screen.blit(title, (area.x + (area.w - title.get_width()) // 2, area.y + 8))

        # Subtitle: formula
        sub = self.fsm.render("case_idx = v0 + v1·4 + v2·16 + v3·64 + w·256   |   T=4 типа, 4 ребра, 12 точек на ячейку", True, TEXT_SEC)
        self.screen.blit(sub, (area.x + (area.w - sub.get_width()) // 2, area.y + 36))

        # Nav bar
        cases = self._get_cases_list()
        pages = max(1, (len(cases) + 15) // 16)
        self.case_page = max(0, min(self.case_page, pages - 1))
        nav_y = area.y + 56
        # Position nav buttons
        nx = area.centerx - 120
        self.btn_prev.rect.topleft = (nx, nav_y)
        self.btn_next.rect.topleft = (nx + 140, nav_y)
        self.btn_wfilter.rect.topleft = (nx + 44, nav_y)
        self.btn_prev.draw(self.screen)
        self.btn_next.draw(self.screen)
        self.btn_wfilter.draw(self.screen)
        page_lbl = self.fmd.render(f"{self.case_page + 1} / {pages}", True, TEXT_CLR)
        self.screen.blit(page_lbl, (nx + 82, nav_y + (32 - page_lbl.get_height()) // 2))

        # Grid of 16 cases
        top_y = nav_y + 40
        avail_h = area.bottom - top_y - 10
        avail_w = area.w - 40
        label_h = 35
        row_gap = label_h + 4
        cell = min(165, (avail_w - 30) // 4, (avail_h - 30 - label_h) // 4)
        gw = 4 * cell + 3 * 10
        gh = 4 * cell + 3 * 10 + 3 * row_gap
        gx = area.x + (area.w - gw) // 2
        gy = top_y + max(0, (avail_h - gh) // 2)

        start = self.case_page * 16
        for i in range(16):
            ci_abs = start + i
            if ci_abs >= len(cases):
                break
            ci = cases[ci_abs]
            col, row = i % 4, i // 4
            cx = gx + col * (cell + 10)
            cy = gy + row * (cell + 10 + row_gap)
            self._draw_case_cell(cx, cy, cell, ci)

    def _draw_case_cell(self, cx, cy, size, case_idx):
        if case_idx not in self.ms_table:
            return
        rect = pygame.Rect(cx, cy, size, size)

        # Decode case
        w_val = case_idx // 256
        rem = case_idx % 256
        v3 = rem // 64; rem %= 64
        v2 = rem // 16; rem %= 16
        v1 = rem // 4
        v0 = rem % 4
        vals = [v0, v1, v2, v3]

        # Shadow
        pygame.draw.rect(self.screen, (210, 212, 218),
                         pygame.Rect(cx + 2, cy + 2, size, size), border_radius=8)
        # Background
        pygame.draw.rect(self.screen, PANEL_BG, rect, border_radius=8)
        pygame.draw.rect(self.screen, BORDER, rect, 1, border_radius=8)

        pad = size * 0.18
        inner = pygame.Rect(cx + pad, cy + pad, size - 2 * pad, size - 2 * pad)

        # Corner positions
        vtx = [
            (inner.left, inner.top),
            (inner.right, inner.top),
            (inner.right, inner.bottom),
            (inner.left, inner.bottom),
        ]

        # Weights for 12-point interpolation (derived from material type)
        weights = [0.1 * (v + 1) for v in vals]
        pts = compute_12_points(0, 0, weights[0], weights[1], weights[2], weights[3])

        # Transform pts to pixel coords
        def to_px(p):
            px = inner.left + p[0] * inner.width
            py = inner.top + p[1] * inner.height
            return (int(px), int(py))

        # Draw filled triangles for each block
        blocks = self.ms_table[case_idx]
        for bi in range(4):
            fill_clr = CASE_FILL[vals[bi]]
            for tri in blocks[bi]:
                if tri == [0, 0, 0]:
                    continue
                pp = [to_px(pts[tri[0]]), to_px(pts[tri[1]]), to_px(pts[tri[2]])]
                try:
                    pygame.draw.polygon(self.screen, fill_clr, pp)
                    pygame.draw.polygon(self.screen, CASE_COLORS[vals[bi]], pp, 2)
                except Exception:
                    pass

        # Draw edge intersection points
        used = set()
        for bi in range(4):
            for tri in blocks[bi]:
                for vi in tri:
                    if vi >= 4 and vi != 0:
                        used.add(vi)
        for ei in used:
            if 4 <= ei <= 7:
                pygame.draw.circle(self.screen, (50, 50, 55), to_px(pts[ei]), 3)
            elif 8 <= ei <= 11:
                pygame.draw.circle(self.screen, (50, 50, 55), to_px(pts[ei]), 3)

        # Draw corner vertices
        vr = max(8, int(size * 0.08))
        for vi in range(4):
            pos = (int(vtx[vi][0]), int(vtx[vi][1]))
            c = CASE_COLORS[vals[vi]]
            pygame.draw.circle(self.screen, c, pos, vr)
            lbl = self.fsm.render(str(vals[vi]), True, (255, 255, 255))
            self.screen.blit(lbl, (pos[0] - lbl.get_width() // 2,
                                    pos[1] - lbl.get_height() // 2))

        # Labels below cell
        lbl = self.fsm.render(f"#{case_idx}", True, TEXT_CLR)
        lx = cx + (size - lbl.get_width()) // 2
        ly = cy + size + 2
        self.screen.blit(lbl, (lx, ly))
        bits = f"{v0}{v1}{v2}{v3} w={w_val}"
        lbl2 = self.fsm.render(bits, True, TEXT_SEC)
        self.screen.blit(lbl2, (cx + (size - lbl2.get_width()) // 2, ly + lbl.get_height()))

    # ========== MAP VIEW ==========
    def _draw_map_view(self):
        if self.map_dirty:
            self._render_map_surface()

        area = pygame.Rect(0, UI_BAR_H, self.screen.get_width(),
                           self.screen.get_height() - UI_BAR_H - STATUS_H)
        self.screen.set_clip(area)

        sw = self.map_surface.get_width()
        sh = self.map_surface.get_height()
        bx = area.x + (area.w - sw) // 2 + int(self.cam_x)
        by = area.y + (area.h - sh) // 2 + int(self.cam_y)
        self.screen.blit(self.map_surface, (bx, by))

        # Debug overlay
        if self.debug_mode > 0 and hasattr(self, 'cell_px') and self.cell_px > 6:
            self._draw_debug(area, bx, by)

        self.screen.set_clip(None)
        self._draw_legend(area)

    def _draw_debug(self, area, ox, oy):
        size = MAP_SIZES[self.map_size_idx]
        h = size + 1
        cell = self.cell_px
        vr = max(3, min(12, cell // 3))

        for y in range(h):
            for x in range(h):
                px = ox + x * cell + 1
                py = oy + y * cell + 1
                if px < area.left - vr or px > area.right + vr:
                    continue
                if py < area.top - vr or py > area.bottom + vr:
                    continue
                pos = (int(px), int(py))
                hval = self.heightmap[y][x]
                midx = self.mat_map[y][x]

                # Background circle
                pygame.draw.circle(self.screen, MAT_COLORS[midx], pos, vr + 1)
                pygame.draw.circle(self.screen, (50, 50, 55), pos, vr + 1, 1)

                if cell >= 18:
                    if self.debug_mode == 1:
                        txt = f"{hval:.2f}"
                    else:
                        txt = MAT_NAMES[midx][:3]
                    ts = self.fsm.render(txt, True, (30, 30, 35))
                    bg = pygame.Surface((ts.get_width() + 2, ts.get_height() + 2), pygame.SRCALPHA)
                    bg.fill((255, 255, 255, 185))
                    self.screen.blit(bg, (pos[0] - ts.get_width() // 2 - 1,
                                          pos[1] - ts.get_height() // 2 - 1))
                    self.screen.blit(ts, (pos[0] - ts.get_width() // 2,
                                          pos[1] - ts.get_height() // 2))
                else:
                    txt = str(midx) if self.debug_mode == 2 else f"{int(hval * 9)}"
                    ts = self.fsm.render(txt, True, (30, 30, 35))
                    self.screen.blit(ts, (pos[0] - ts.get_width() // 2,
                                          pos[1] - ts.get_height() // 2))

    def _draw_legend(self, area):
        lx = area.right - 160
        ly = area.top + 10
        lw, lh = 150, 148
        s = pygame.Surface((lw, lh), pygame.SRCALPHA)
        s.fill((255, 255, 255, 210))
        self.screen.blit(s, (lx, ly))
        pygame.draw.rect(self.screen, BORDER, (lx, ly, lw, lh), 1, border_radius=6)
        ts = self.fmd.render("Материалы", True, TEXT_CLR)
        self.screen.blit(ts, (lx + 8, ly + 6))
        for i in range(5):
            iy = ly + 28 + i * 23
            pygame.draw.rect(self.screen, MAT_COLORS[i], (lx + 10, iy, 14, 14), border_radius=2)
            pygame.draw.rect(self.screen, BORDER, (lx + 10, iy, 14, 14), 1, border_radius=2)
            if i == 0:
                thr = f"< {THRESHOLDS[0]:.2f}"
            elif i < len(THRESHOLDS):
                thr = f"{THRESHOLDS[i-1]:.2f}-{THRESHOLDS[i]:.2f}"
            else:
                thr = f">= {THRESHOLDS[-1]:.2f}"
            label = f"{MAT_NAMES[i]} ({thr})"
            ts = self.fsm.render(label, True, TEXT_CLR)
            self.screen.blit(ts, (lx + 30, iy - 1))

    # ========== MAIN LOOP ==========
    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit(0)


# ================================================================
# ENTRY POINT
# ================================================================
if __name__ == "__main__":
    try:
        app = App()
        app.run()
    except Exception as e:
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)
