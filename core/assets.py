import sys
import os


def resource_path(relative_path):
    """Get absolute path to resource"""

    # Check if running in a PyInstaller bundle
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)

    # Otherwise, return the path relative to the current working directory
    return os.path.join(os.getcwd(), relative_path)


class ASSETS:
    PRIMOGEMS_ICON = resource_path("assets/primogem.webp")
    FATES_ICON = resource_path("assets/fate.webp")
    STARGLITTER_ICON = resource_path("assets/starglitter.webp")
    CRYSTAL_ICON = resource_path("assets/crystal.webp")
    APP_ICON = resource_path("assets/icon.png")
