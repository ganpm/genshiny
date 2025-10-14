import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
import qdarktheme
from ui.MainWindow import MainWindow
from core.config import CONFIG


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont(CONFIG.FONT_FAMILY, CONFIG.FONT_SIZE, QFont.Weight.Medium))
    qdarktheme.setup_theme()
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
