from PyQt6.QtWidgets import (
    QComboBox,
)


class BooleanComboBox(QComboBox):

    def __init__(
            self,
            parent=None,
            current_index: int = 0,
            editable: bool = False,
            width: int = 100
            ):

        super().__init__(parent)
        self.addItems(['No', 'Yes'])
        self.setCurrentIndex(current_index)
        self.setEditable(editable)
        self.setFixedWidth(width)
        self.resize(self.sizeHint())

    def value(self) -> bool:
        return self.currentText() == 'Yes'
