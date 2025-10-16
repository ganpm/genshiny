from PyQt6.QtWidgets import (
    QSpinBox,
)
from PyQt6.QtCore import (
    Qt,
    QEvent,
)
from PyQt6.QtGui import (
    QEnterEvent,
)


class CountSpinbox(QSpinBox):

    def __init__(self, parent=None):

        super().__init__(parent)
        self.init_UI()

    def init_UI(self):

        self.setRange(0, 999999)
        self.setSingleStep(1)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.setFixedWidth(120)
        self.setFixedHeight(30)
        # self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def enterEvent(self, event: QEnterEvent) -> None:

        self.setFocus()
        # If readonly or disabled, set cursor to normal
        if self.isReadOnly() or not self.isEnabled():
            self.setCursor(Qt.CursorShape.ArrowCursor)
        # If enabled and not readonly, select all text
        if not self.isReadOnly() and self.isEnabled():
            self.lineEdit().selectAll()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:

        self.clearFocus()
        # Always reset mouse cursor when leaving
        self.setCursor(Qt.CursorShape.ArrowCursor)
        # If enabled and not readonly, deselect text
        if not self.isReadOnly() and self.isEnabled():
            self.lineEdit().deselect()
        super().leaveEvent(event)
