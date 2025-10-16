# Compilation Settings for Nuitka
#
# nuitka-project-if: {OS} in ("Windows", "Linux", "Darwin", "FreeBSD"):
#    nuitka-project: --mode=onefile
# nuitka-project-else:
#    nuitka-project: --mode=standalone
#
# nuitka-project-if: {OS} in ("Windows"):
#    nuitka-project: --windows-icon-from-ico={MAIN_DIRECTORY}/assets/icon.ico
#    nuitka-project: --windows-console-mode=disable
#
# nuitka-project: --enable-plugins=pyqt6
# nuitka-project: --include-data-dir={MAIN_DIRECTORY}/assets=assets

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
