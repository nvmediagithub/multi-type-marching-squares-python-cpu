"""MTMS — Multi-Type Marching Squares Visualization Package.

Provides a modular architecture for the research visualization tool based on:
  "Математическая модель и алгоритм много-типовых марширующих квадратов"
  Н. С. Васильев, Н. Н. Иванова

Package structure:
  mtms.config      — centralized configuration (Display, Theme, Materials, etc.)
  mtms.algorithm   — pure algorithm core (table generation, normalization, interpolation)
  mtms.terrain     — numpy-based terrain generation (Perlin noise, heightmaps)
  mtms.ui          — Pygame UI components (Button, Dropdown, fonts)
  mtms.renderer    — rendering layer (cases view, map view, toolbar)
  mtms.app         — thin orchestrator (event loop, state management, camera)
"""
from mtms.config import DEFAULT_CONFIG, Config

__all__ = ["DEFAULT_CONFIG", "Config"]
