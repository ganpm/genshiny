import sys
import math

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QWidget,
    QLayout,
    QLabel,
)


def set_titlebar_darkmode(widget: QWidget):
    if sys.platform == 'win32':
        # Windows 10/11 dark titlebar via dwm API
        try:
            from ctypes import windll, c_int, byref, sizeof
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            windll.dwmapi.DwmSetWindowAttribute(
                int(widget.winId()),
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                byref(c_int(1)),
                sizeof(c_int)
            )
        except Exception as e:
            print(f"Failed to set dark titlebar: {e}")
    if sys.platform == 'darwin':
        # On macOS, titlebar is dark by default
        widget.setUnifiedTitleAndToolBarOnMac(True)


def left_aligned_layout(
        *widgets: QWidget | QLayout
        ) -> QHBoxLayout:

    box = QHBoxLayout()
    box.setSpacing(0)
    for widget in widgets:
        if isinstance(widget, QLayout):
            box.addLayout(widget)
        elif isinstance(widget, str):
            # If string, add as a label
            box.addWidget(QLabel(widget))
        else:
            try:
                box.addWidget(widget)
            except Exception as e:
                print(f"Failed to add widget: {e}")
                continue
    box.addStretch(1)
    return box


def right_aligned_layout(
        *widgets: QWidget | QLayout
        ) -> QHBoxLayout:

    box = QHBoxLayout()
    box.setSpacing(0)
    box.addStretch(1)
    for widget in widgets:
        if isinstance(widget, QLayout):
            box.addLayout(widget)
        else:
            try:
                box.addWidget(widget)
            except Exception as e:
                print(f"Failed to add widget: {e}")
                continue
    return box


def cmap(
        p: float,
        normalization_method: str = 'quadratic',
        cutoff: float = 0.0,
        cutoff_intensity: int = 30,
        min_intensity: int = 40,
        max_intensity: int = 215,
        ) -> tuple[int, int, int]:
    """Color map from probability to color (RGB tuple). Used in visualizing the probability values in the joint distribution."""

    if p <= cutoff:
        k = cutoff_intensity
        return (0, k, k)

    match normalization_method:
        case 'linear':
            x = p
        case 'sqrt':
            x = p ** 0.5
        case 'quadratic':
            x = (1 - (p-1) ** 2) ** 0.5
        case 'log':
            x = math.log10(9 * p + 1)
        case _:
            raise ValueError(f"Unknown norm type: {normalization_method}")
    k = int(min_intensity + (max_intensity - min_intensity) * x)

    return (0, k, k)
