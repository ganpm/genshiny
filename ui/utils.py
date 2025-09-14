import sys

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QWidget,
    QLayout,
    QLabel,
)


def set_titlebar_darkmode(widget):
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
