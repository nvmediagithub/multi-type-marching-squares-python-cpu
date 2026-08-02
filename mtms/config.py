"""Centralized configuration for the MTMS viewer."""
from dataclasses import dataclass, field


# ================================================================
# Display Configuration
# ================================================================
@dataclass(frozen=True)
class DisplayConfig:
    screen_width: int = 1280
    screen_height: int = 800
    fps: int = 60
    ui_bar_height: int = 50
    status_bar_height: int = 26


# ================================================================
# Theme Configuration (Light Theme)
# ================================================================
@dataclass(frozen=True)
class ThemeConfig:
    bg_color: tuple[int, int, int] = (240, 241, 245)
    panel_bg: tuple[int, int, int] = (255, 255, 255)
    text_color: tuple[int, int, int] = (35, 35, 40)
    text_secondary: tuple[int, int, int] = (120, 122, 130)
    accent: tuple[int, int, int] = (65, 125, 215)
    accent_text: tuple[int, int, int] = (255, 255, 255)
    button_color: tuple[int, int, int] = (225, 228, 235)
    button_hover: tuple[int, int, int] = (210, 215, 225)
    border: tuple[int, int, int] = (208, 210, 218)
    grid_line: tuple[int, int, int] = (222, 224, 232)


# ================================================================
# Material Configuration (5 global terrain types)
# ================================================================
@dataclass(frozen=True)
class MaterialConfig:
    num_global_types: int = 5
    colors: list[tuple[int, int, int]] = field(default_factory=lambda: [
        (70, 150, 220),   # 0: Water (blue)
        (215, 195, 105),  # 1: Sand (yellow)
        (95, 185, 95),    # 2: Grass (green)
        (145, 143, 143),  # 3: Rocks (grey)
        (235, 235, 242),  # 4: Snow (white)
    ])
    names: list[str] = field(default_factory=lambda: [
        "Вода", "Песок", "Трава", "Скалы", "Снег"
    ])
    thresholds: tuple[float, ...] = field(
        default_factory=lambda: (0.25, 0.40, 0.65, 0.85)
    )


# ================================================================
# Case View Colors (abstract colors for types 0..3 in cases view)
# ================================================================
@dataclass(frozen=True)
class CaseViewConfig:
    fill_colors: list[tuple[int, int, int]] = field(default_factory=lambda: [
        (190, 218, 245),
        (195, 238, 195),
        (248, 228, 185),
        (230, 200, 230),
    ])
    stroke_colors: list[tuple[int, int, int]] = field(default_factory=lambda: [
        (55, 120, 200),   # 0: Blue
        (50, 165, 50),    # 1: Green
        (200, 140, 40),   # 2: Orange
        (160, 55, 160),   # 3: Purple
    ])


# ================================================================
# Algorithm Configuration
# ================================================================
@dataclass(frozen=True)
class AlgorithmConfig:
    num_types: int = 4  # T — number of material types in the lookup table
    map_sizes: tuple[int, ...] = field(default_factory=lambda: (16, 32, 64, 128))


# ================================================================
# Top-level Config
# ================================================================
@dataclass(frozen=True)
class Config:
    display: DisplayConfig = field(default_factory=DisplayConfig)
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    materials: MaterialConfig = field(default_factory=MaterialConfig)
    cases: CaseViewConfig = field(default_factory=CaseViewConfig)
    algorithm: AlgorithmConfig = field(default_factory=AlgorithmConfig)


# Default configuration instance
DEFAULT_CONFIG = Config()
