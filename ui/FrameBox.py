from PyQt6.QtWidgets import (
    QFrame,
)


class FrameBox(QFrame):

    def __init__(self, parent=None):

        super().__init__(parent)
        self.init_UI()

    def init_UI(self):

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
