import sys
from pathlib import Path

from core.containers import WidgetGeometry


class CONFIG:

    POSITION_X = 1300
    POSITION_Y = 100
    POSITION = (POSITION_X, POSITION_Y)
    WIDTH = 400
    HEIGHT = 780
    SIZE = (WIDTH, HEIGHT)
    GEOMETRY = (POSITION_X, POSITION_Y, WIDTH, HEIGHT)

    ICON_HEIGHT = 30
    ICON_WIDTH = 30
    ICON_SIZE = (ICON_WIDTH, ICON_HEIGHT)

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

    SIM_WIDTH = 1080
    SIM_HEIGHT = 860
    SIM_SIZE = (SIM_WIDTH, SIM_HEIGHT)

    CHART = WidgetGeometry(70, 10, 660, 180)
