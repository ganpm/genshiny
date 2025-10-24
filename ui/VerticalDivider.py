from PyQt6.QtWidgets import (
    QFrame,
)


class VerticalDivider(QFrame):

    def __init__(self, parent=None):

        super(VerticalDivider, self).__init__(parent)
        self.setFrameShape(QFrame.Shape.VLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
