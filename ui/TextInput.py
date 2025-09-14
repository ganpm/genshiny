from PyQt6.QtWidgets import (
    QLineEdit,
)
from PyQt6.QtCore import (
    Qt,
)


class TextInput(QLineEdit):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_UI()

    def init_UI(self):
        # Do not focus on this widget on load
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
