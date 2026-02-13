#!/usr/bin/env python3
"""Entry point for PyInstaller bundle - launches the GUI application."""

import sys
from pathlib import Path

# Add project root to path so src package can be imported
if getattr(sys, "frozen", False):
    # Running as PyInstaller bundle - src is in _MEIPASS
    base = Path(sys._MEIPASS)
else:
    # Running from source
    base = Path(__file__).parent

sys.path.insert(0, str(base))

# Now import and run - this will work because src is in the path
from src.gui import run_gui

if __name__ == "__main__":
    run_gui()
