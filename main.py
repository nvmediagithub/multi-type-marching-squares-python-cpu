#!/usr/bin/env python3
"""Multi-Type Marching Squares — Research Visualization Tool.

New modular entry point. Launches the MTMS Viewer application via the
mtms package (decomposed from marching_squares_viewer_2.0.py).

Usage:
    python main.py          # default configuration
    python -m pytest mtms/  # run unit tests (no display needed)

Original standalone file:
    python marching_squares_viewer_2.0.py   # also works, identical output
"""
import sys
import traceback


def main() -> None:
    from mtms.app import MTMSApp
    app = MTMSApp()
    app.run()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
