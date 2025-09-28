from PyQt6.QtWidgets import (
    QComboBox,
)


class Dropdown(QComboBox):

    def __init__(
            self,
            parent=None,
            options: list[str] = None,
            current_index: int = 0,
            editable: bool = False,
            width: int = 100
            ):

        super().__init__(parent)
        self.addItems(options if options else [''])
        self.setCurrentIndex(current_index)
        self.setEditable(editable)
        self.setFixedWidth(width)
        self.resize(self.sizeHint())
