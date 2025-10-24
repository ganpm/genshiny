from PyQt6.QtWidgets import (
    QFrame,
)


class HorizontalDivider(QFrame):

    def __init__(self, parent=None):

        super(HorizontalDivider, self).__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
