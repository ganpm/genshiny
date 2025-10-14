# Genshiny

Genshiny is a small desktop application for managing and analyzing your pulls in Genshin Impact.

# Features

- Track your Primogems, Intertwined Fates, Masterless Starglitter, and Genesis Crystals offline.
- Simple, user-friendly interface.
- Save and load your currency data.
- Calculate how many pulls you currently have.
- NEW: Count how many guaranteed 5 stars you can get based on your total pulls.

# Requirements

Only available in Windows OS (for now). The executable itself has no requirements to run. Its all in one file.

The source code is made using Python 3.12.2, PyQt6, and PyQt6-Charts. The EXE is built using pyinstaller.

## Notes

If there is an error installing `pyqtdarktheme` through pip install, or if `pyqtdarktheme.setup_theme()` does not work, or `pyqtdarktheme` version is `0.1.7` instead of `2.1.0`, install it manually using the following command:

```
pip install pyqtdarktheme==2.1.0 --ignore-requires-python
```

Reference:
https://github.com/5yutan5/PyQtDarkTheme/issues/252

## Build Command

The executable is built using Nuitka.

### Windows
```sh
python -m nuitka --onefile --enable-plugins=pyqt6 --include-data-dir="assets=assets" --windows-icon-from-ico=assets/icon.ico --windows-console-mode=disable --product-name=Genshiny --product-version=2025.10.14.0 Genshiny.py
```
