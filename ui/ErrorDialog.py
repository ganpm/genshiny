from __future__ import annotations
import traceback

from PyQt6.QtWidgets import (
    QGridLayout,
)
from PyQt6.QtWidgets import (
    QMessageBox,
    QLabel,
    QTextEdit,
)


class ErrorDialog(QMessageBox):
    def __init__(self, message: str = ''):
        super().__init__()
        traceback_text = traceback.format_exc()
        self.setWindowTitle("Error Occurred")

        layout: QGridLayout = self.layout()

        self.message_label = QLabel(message)
        layout.addWidget(self.message_label, 0, 0, 1, layout.columnCount())

        self.traceback_edit = QTextEdit()
        self.traceback_edit.setReadOnly(True)
        self.traceback_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.traceback_edit.setText(traceback_text)
        self.traceback_edit.setFixedSize(600, 300)
        layout.addWidget(self.traceback_edit, 1, 0, 1, layout.columnCount())

        self.setStandardButtons(QMessageBox.StandardButton.Ok)
        self.exec()
