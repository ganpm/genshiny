from PyQt6.QtWidgets import (
    QTableWidget,
    QHeaderView,
    QTableWidgetItem,
)
from PyQt6.QtCore import (
    Qt,
)
from PyQt6.QtGui import QColor

import numpy as np

import math


class Heatmap(QTableWidget):

    def __init__(self, parent=None):

        super(Heatmap, self).__init__(parent)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def clear_heatmap(self):

        self.clear()
        self.setRowCount(0)
        self.setColumnCount(0)

    def set_heatmap_data(
            self,
            x_labels: list[int],
            y_labels: list[int],
            data: np.ndarray,
            ) -> None:

        r = len(y_labels)
        c = len(x_labels)

        self.setRowCount(r)
        self.setColumnCount(c)

        self.setHorizontalHeaderLabels([str(x) for x in x_labels])
        self.setVerticalHeaderLabels([str(y) for y in y_labels])

        for x in range(c):
            for y in range(r):
                value = data[y, x]
                text = f"{value*100:>8.4f}" if value > 0 else ""
                item = QTableWidgetItem(text)
                # Make the text larger
                font = item.font()
                font.setPointSize(12)
                item.setFont(font)
                # Make item unselectable
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
                # Color code based on probability
                color = QColor(*cmap(value))
                item.setBackground(color)
                self.setItem(y, x, item)


def cmap(
        p: float,
        normalization_method: str = 'quadratic',
        cutoff: float = 0.0,
        cutoff_intensity: int = 30,
        min_intensity: int = 40,
        max_intensity: int = 215,
        ) -> tuple[int, int, int]:
    """Color map from probability to color (RGB tuple). Used in visualizing the probability values in the joint distribution."""

    if p <= cutoff:
        k = cutoff_intensity
        return (0, k, k)

    match normalization_method:
        case 'linear':
            x = p
        case 'sqrt':
            x = p ** 0.5
        case 'quadratic':
            x = (1 - (p-1) ** 2) ** 0.5
        case 'log':
            x = math.log10(9 * p + 1)
        case _:
            raise ValueError(f"Unknown norm type: {normalization_method}")
    k = int(min_intensity + (max_intensity - min_intensity) * x)

    return (0, k, k)
