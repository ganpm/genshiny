import sys

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
        *items: QWidget | QLayout | str
        ) -> QHBoxLayout:

    box = QHBoxLayout()
    box.setSpacing(0)
    for item in items:
        if isinstance(item, QLayout):
            box.addLayout(item)
        elif isinstance(item, str):
            box.addWidget(QLabel(item))
        elif isinstance(item, QWidget):
            box.addWidget(item)
        else:
            raise ValueError(f"Failed to add item type: {type(item)}")
    box.addStretch(1)
    return box


def right_aligned_layout(
        *items: QWidget | QLayout | str
        ) -> QHBoxLayout:

    box = QHBoxLayout()
    box.setSpacing(0)
    box.addStretch(1)
    for item in items:
        if isinstance(item, QLayout):
            box.addLayout(item)
        elif isinstance(item, str):
            box.addWidget(QLabel(item))
        elif isinstance(item, QWidget):
            box.addWidget(item)
        else:
            raise ValueError(f"Failed to add item type: {type(item)}")
    return box


def center_aligned_layout(
        *items: QWidget | QLayout | str
        ) -> QHBoxLayout:

    box = QHBoxLayout()
    box.setSpacing(0)
    box.addStretch(1)
    for item in items:
        if isinstance(item, QLayout):
            box.addLayout(item)
        elif isinstance(item, str):
            box.addWidget(QLabel(item))
        elif isinstance(item, QWidget):
            box.addWidget(item)
        else:
            raise ValueError(f"Failed to add item type: {type(item)}")
    box.addStretch(1)
    return box
