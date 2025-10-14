from core.config import CONFIG


def resource_path(filename: str) -> str:

    return str(CONFIG.ASSETS_PATH / filename)


class ASSETS:

    APP_ICON = resource_path("icon.png")
    PRIMOGEMS_ICON = resource_path("primogem.webp")
    FATES_ICON = resource_path("fate.webp")
    STARGLITTER_ICON = resource_path("starglitter.webp")
    CRYSTAL_ICON = resource_path("crystal.webp")
