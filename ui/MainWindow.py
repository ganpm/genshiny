from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QGridLayout,
)
from PyQt6.QtCore import (
    Qt,
)
from PyQt6.QtGui import (
    QIcon,
)

from .CountSpinbox import CountSpinbox
from .ErrorDialog import ErrorDialog
from .SimulationDialog import SimulationWindow
from .FrameBox import FrameBox
from .BarGraph import BarGraph
from .utils import (
    set_titlebar_darkmode,
    left_aligned_layout,
    right_aligned_layout,
)
from core.config import CONFIG
from core.text import TEXT
from core.assets import ASSETS

import json


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()
        self.initUI()
        self.load_from_last_save()

    def initUI(self):
        """Initialize the main window."""

        set_titlebar_darkmode(self)
        self.setWindowTitle(TEXT.APP_NAME)
        self.setWindowIcon(QIcon(ASSETS.APP_ICON))
        # Set window size and position
        self.setGeometry(*CONFIG.WINDOW.GEOMETRY)
        # Disable resizing
        self.setFixedSize(*CONFIG.WINDOW.SIZE)
        # Disable maximize button
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        # Setup the menu bar
        menu_bar = self.menuBar()
        load_action = menu_bar.addAction(TEXT.LOAD)
        load_action.setShortcut(CONFIG.LOAD_SHORTCUT)
        load_action.triggered.connect(self.load_data)
        save_action = menu_bar.addAction(TEXT.SAVE)
        save_action.setShortcut(CONFIG.SAVE_SHORTCUT)
        save_action.triggered.connect(self.save_data)
        new_action = menu_bar.addAction(TEXT.NEW)
        new_action.setShortcut(CONFIG.NEW_SHORTCUT)
        new_action.triggered.connect(self.new_data)

        # Create the central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)

        # Icons
        def primogems_icon():
            icon = QLabel()
            icon.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            icon.setPixmap(QIcon(ASSETS.PRIMOGEMS_ICON).pixmap(*CONFIG.ICON.SIZE))
            return icon

        def fates_icon():
            icon = QLabel()
            icon.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            icon.setPixmap(QIcon(ASSETS.FATES_ICON).pixmap(*CONFIG.ICON.SIZE))
            return icon

        def starglitter_icon():
            icon = QLabel()
            icon.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            icon.setPixmap(QIcon(ASSETS.STARGLITTER_ICON).pixmap(*CONFIG.ICON.SIZE))
            return icon

        def crystal_icon():
            icon = QLabel()
            icon.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            icon.setPixmap(QIcon(ASSETS.CRYSTAL_ICON).pixmap(*CONFIG.ICON.SIZE))
            return icon

        pull_calculator_label = QLabel(TEXT.PULLS_CALCULATOR)
        pull_calculator_label_font = pull_calculator_label.font()
        pull_calculator_label_font.setBold(True)
        pull_calculator_label.setFont(pull_calculator_label_font)
        layout.addWidget(pull_calculator_label)
        groupbox = FrameBox()
        layout.addWidget(groupbox)

        groupbox_layout = QGridLayout()
        groupbox.setLayout(groupbox_layout)

        self.primogems = CountSpinbox(self)
        self.primogems.valueChanged.connect(self.value_modified)
        box = left_aligned_layout(primogems_icon(), TEXT.PRIMOGEMS)
        groupbox_layout.addLayout(box, 0, 0)
        groupbox_layout.addWidget(self.primogems, 0, 1)

        self.fates = CountSpinbox(self)
        self.fates.valueChanged.connect(self.value_modified)
        box = left_aligned_layout(fates_icon(), TEXT.FATES)
        groupbox_layout.addLayout(box, 1, 0)
        groupbox_layout.addWidget(self.fates, 1, 1)

        self.starglitter = CountSpinbox(self)
        self.starglitter.valueChanged.connect(self.value_modified)
        box = left_aligned_layout(starglitter_icon(), TEXT.STARGLITTER)
        groupbox_layout.addLayout(box, 2, 0)
        groupbox_layout.addWidget(self.starglitter, 2, 1)

        self.crystal = CountSpinbox(self)
        self.crystal.valueChanged.connect(self.value_modified)
        box = left_aligned_layout(crystal_icon(), TEXT.CRYSTAL)
        groupbox_layout.addLayout(box, 3, 0)
        groupbox_layout.addWidget(self.crystal, 3, 1)

        # Display

        groupbox = FrameBox()
        layout.addWidget(groupbox)

        groupbox_layout = QGridLayout()
        groupbox.setLayout(groupbox_layout)

        def display_widget(icon: QLabel) -> tuple[QHBoxLayout, QLabel]:
            display = QLabel()
            display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            display.setFixedWidth(80)
            layout = right_aligned_layout(display, icon)
            layout.addSpacing(10)

            return layout, display

        box = left_aligned_layout(TEXT.FROM, primogems_icon(), TEXT.PRIMOGEMS)
        groupbox_layout.addLayout(box, 0, 0)

        container, self.fates_from_primogems = display_widget(fates_icon())
        groupbox_layout.addLayout(container, 0, 1)

        box = left_aligned_layout(TEXT.FROM, starglitter_icon(), TEXT.STARGLITTER)
        groupbox_layout.addLayout(box, 1, 0)

        container, self.fates_from_starglitter = display_widget(fates_icon())
        groupbox_layout.addLayout(container, 1, 1)

        box = left_aligned_layout(TEXT.FROM, fates_icon(), TEXT.FATES)
        groupbox_layout.addLayout(box, 2, 0)

        container, self.fates_from_inventory = display_widget(fates_icon())
        groupbox_layout.addLayout(container, 2, 1)

        box = left_aligned_layout(TEXT.FROM, crystal_icon(), TEXT.CRYSTAL)
        groupbox_layout.addLayout(box, 3, 0)
        container, self.fates_from_crystal = display_widget(fates_icon())
        groupbox_layout.addLayout(container, 3, 1)

        total_fates_label = QLabel(TEXT.TOTAL_FATES)
        total_fates_label_font = total_fates_label.font()
        total_fates_label_font.setBold(True)
        total_fates_label.setFont(total_fates_label_font)

        box = left_aligned_layout(total_fates_label)
        groupbox_layout.addLayout(box, 4, 0)

        container, self.total_fates = display_widget(fates_icon())
        total_fates_font = self.total_fates.font()
        total_fates_font.setBold(True)
        self.total_fates.setFont(total_fates_font)
        groupbox_layout.addLayout(container, 4, 1)

        # Pity Chart
        self.pity_breakpoints = list(range(72, 91, 3))
        self.pity_count_per_breakpoint = [0 for _ in self.pity_breakpoints]

        max_int_ceil = int(max(self.pity_count_per_breakpoint)) + 2
        min_int_floor = max(int(min(self.pity_count_per_breakpoint)) - 1, 0)

        self.bar_graph = BarGraph(
            geometry=(60, 20, 300, 190),
            title=TEXT.BLANK,
            x_label=TEXT.PITY_BREAKPOINTS,
            y_label=TEXT.PITY_COUNT,
            x_values=[str(bp) for bp in self.pity_breakpoints],
            y_range=(min_int_floor, max_int_ceil),
            y_tick_count=max_int_ceil - min_int_floor + 1,
        )
        layout.addWidget(self.bar_graph)

        layout.addStretch(1)

        self.simulate_button = QPushButton(TEXT.SIMULATE)
        self.simulate_button.clicked.connect(self.simulate)

        layout.addWidget(self.simulate_button)

        # Set tab order for spinboxes

        self.setTabOrder(self.primogems, self.fates)
        self.setTabOrder(self.fates, self.starglitter)
        self.setTabOrder(self.starglitter, self.crystal)

    def validate_data(self, raw_data: dict) -> dict:
        """Validate the data structure."""

        data = {
            TEXT.PRIMOGEMS: raw_data.get(TEXT.PRIMOGEMS, 0),
            TEXT.FATES: raw_data.get(TEXT.FATES, 0),
            TEXT.STARGLITTER: raw_data.get(TEXT.STARGLITTER, 0),
            TEXT.CRYSTAL: raw_data.get(TEXT.CRYSTAL, 0),
        }
        return data

    def load_data(self):
        """Open a file dialog to load data from a JSON file."""

        if not CONFIG.SAVE_PATH.exists():
            CONFIG.SAVE_PATH.mkdir(parents=True, exist_ok=True)
        starting_dir = str(CONFIG.SAVE_PATH)
        open_dir, _ = QFileDialog.getOpenFileName(
            self, TEXT.OPEN_FILE_CAPTION, starting_dir, TEXT.FILE_FILTER)
        if not open_dir:
            return
        # Load the JSON file
        with open(open_dir, 'r') as file:
            raw_data: dict = json.load(file)
        # Validate the data structure
        data = self.validate_data(raw_data)
        # Set the data to the UI
        try:
            self.set_data(data)
        except Exception:
            ErrorDialog(TEXT.OPEN_FAILED)

    def save_data(self):
        """Open a file dialog to save data to a JSON file."""

        if not CONFIG.SAVE_PATH.exists():
            CONFIG.SAVE_PATH.mkdir(parents=True, exist_ok=True)
        starting_dir = str(CONFIG.SAVE_PATH)
        save_dir, _ = QFileDialog.getSaveFileName(
            self, TEXT.SAVE_FILE_CAPTION, starting_dir, TEXT.FILE_FILTER)
        if not save_dir:
            return
        data = self.get_data()
        with open(save_dir, 'w') as file:
            json.dump(data, file, indent=4)

    def new_data(self):
        """Clear the data."""

        self.primogems.setValue(0)
        self.fates.setValue(0)
        self.starglitter.setValue(0)
        self.crystal.setValue(0)

    def get_data(self):
        """Get the data from the UI."""

        data = {
            TEXT.PRIMOGEMS: self.primogems.value(),
            TEXT.FATES: self.fates.value(),
            TEXT.STARGLITTER: self.starglitter.value(),
            TEXT.CRYSTAL: self.crystal.value(),
        }
        return data

    def set_data(self, data: dict):
        """Set the data to the UI."""

        self.primogems.setValue(data.get(TEXT.PRIMOGEMS, 0))
        self.fates.setValue(data.get(TEXT.FATES, 0))
        self.starglitter.setValue(data.get(TEXT.STARGLITTER, 0))
        self.crystal.setValue(data.get(TEXT.CRYSTAL, 0))
        self.value_modified()

    def load_from_last_save(self):
        """Load the last save file."""

        if not CONFIG.SAVE_PATH.exists():
            CONFIG.SAVE_PATH.mkdir(parents=True, exist_ok=True)

        save_file = CONFIG.LAST_SAVE_FILE

        # If file does not exist, create it
        if not save_file.exists():
            self.save_to_last_save()
            return

        # Load the last save file
        with open(save_file, 'r') as file:
            data = json.load(file)
        # Validate the data structure
        data = self.validate_data(data)
        # Set the data to the UI
        try:
            self.set_data(data)
        except Exception:
            pass

    def save_to_last_save(self):
        """Save the current data to the last save file."""

        save_file = CONFIG.LAST_SAVE_FILE
        data = self.get_data()
        with open(save_file, 'w') as file:
            json.dump(data, file, indent=4)

    def value_modified(self):
        """Calculate the converted materials when the required materials are modified."""

        primogems = self.primogems.value()
        fates = self.fates.value()
        starglitter = self.starglitter.value()

        fates_from_primogems = primogems // 160
        self.fates_from_primogems.setText(str(fates_from_primogems))

        fates_from_starglitter = starglitter // 5
        self.fates_from_starglitter.setText(str(fates_from_starglitter))

        fates_from_inventory = fates
        self.fates_from_inventory.setText(str(fates_from_inventory))

        fates_from_crystal = self.crystal.value() // 160
        self.fates_from_crystal.setText(str(fates_from_crystal))

        total_fates = (
            fates_from_primogems +
            fates_from_starglitter +
            fates_from_inventory +
            fates_from_crystal)
        self.total_pulls = total_fates
        self.total_fates.setText(str(total_fates))

        # Update the pity chart
        self.pity_count_per_breakpoint = [round(total_fates / i, 2) for i in self.pity_breakpoints]

        new_data = {
            bp: round(total_fates / bp, 2)
            for bp in self.pity_breakpoints
        }
        self.bar_graph.update_data(new_data)

        # Update y-axis range to fit the new data
        max_int_ceil = int(max(self.pity_count_per_breakpoint)) + 2
        min_int_floor = max(int(min(self.pity_count_per_breakpoint)) - 1, 0)
        self.bar_graph._y_axis.setRange(min_int_floor, max_int_ceil)
        self.bar_graph._y_axis.setTickCount(max_int_ceil - min_int_floor + 1)

        self.save_to_last_save()

    def simulate(self):
        """Simulate pulls based on the available fates."""

        dialog = SimulationWindow(pulls=self.total_pulls)
        dialog.show()
