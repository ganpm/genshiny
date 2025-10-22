import sys
from pathlib import Path

from core.containers import Box


class CONFIG:

    WINDOW = Box(x=1300, y=100, w=400, h=780)

    ICON = Box(w=30, h=30)

    INSIDE_PATH = Path(__file__).parent.parent
    ASSETS_PATH = INSIDE_PATH / "assets"

    OUTSIDE_PATH = Path(sys.argv[0]).parent
    SAVE_PATH = OUTSIDE_PATH / "save"
    LAST_SAVE_FILE = SAVE_PATH / "last_save.json"

    FONT_FAMILY = "Segoe UI"
    FONT_SIZE = 12

    LOAD_SHORTCUT = "Ctrl+O"
    SAVE_SHORTCUT = "Ctrl+S"
    NEW_SHORTCUT = "Ctrl+N"

    SIMULATION = Box(w=1080, h=900)

    CHART = Box(x=70, y=20, w=640, h=170)
