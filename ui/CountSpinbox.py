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
        # Do not focus on this widget on load
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def enterEvent(self, event: QEnterEvent) -> None:
        self.setFocus()
        # If readonly, set cursor to normal
        if self.isReadOnly():
            self.setCursor(Qt.CursorShape.ArrowCursor)
        if not self.isReadOnly():
            self.lineEdit().selectAll()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.clearFocus()
        # Reset mouse cursor
        self.setCursor(Qt.CursorShape.ArrowCursor)
        if not self.isReadOnly():
            # clear the highlight
            self.lineEdit().deselect()
        super().leaveEvent(event)
