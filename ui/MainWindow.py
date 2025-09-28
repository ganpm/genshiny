from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    # QDialogButtonBox,
    QPushButton,
    QFileDialog,
    QGridLayout,
)
from PyQt6.QtCore import (
    Qt,
    QRectF,
)
from PyQt6.QtGui import (
    QIcon,
    QPainter,
)
from PyQt6.QtCharts import (
    QChart,
    QChartView,
    QBarSeries,
    QBarSet,
    QValueAxis,
    QBarCategoryAxis,
)

from .CountSpinbox import CountSpinbox
from .ErrorDialog import ErrorDialog
from .SimulationDialog import SimulationDialog
from .utils import (
    set_titlebar_darkmode,
    left_aligned_layout,
    right_aligned_layout,
)
from core.config import CONFIG
from core.text import TEXT
from core.assets import ASSETS

import os
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
        self.setGeometry(*CONFIG.GEOMETRY)
        # Disable resizing
        self.setFixedSize(*CONFIG.SIZE)
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
            icon.setPixmap(QIcon(ASSETS.PRIMOGEMS_ICON).pixmap(*CONFIG.ICON_SIZE))
            return icon

        def fates_icon():
            icon = QLabel()
            icon.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            icon.setPixmap(QIcon(ASSETS.FATES_ICON).pixmap(*CONFIG.ICON_SIZE))
            return icon

        def starglitter_icon():
            icon = QLabel()
            icon.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            icon.setPixmap(QIcon(ASSETS.STARGLITTER_ICON).pixmap(*CONFIG.ICON_SIZE))
            return icon

        def crystal_icon():
            icon = QLabel()
            icon.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            icon.setPixmap(QIcon(ASSETS.CRYSTAL_ICON).pixmap(*CONFIG.ICON_SIZE))
            return icon

        # Inventory
        layout.addWidget(QLabel("<b>Pulls Calculator</b>"))
        groupbox = QGroupBox()
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

        groupbox = QGroupBox()
        layout.addWidget(groupbox)

        groupbox_layout = QGridLayout()
        groupbox.setLayout(groupbox_layout)

        def display_widget(icon: QLabel) -> tuple[QHBoxLayout, QLabel]:
            display = QLabel("0")
            display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            display.setFixedWidth(80)
            layout = right_aligned_layout(display, icon)
            layout.addSpacing(10)

            return layout, display

        box = left_aligned_layout("From", primogems_icon(), TEXT.PRIMOGEMS)
        groupbox_layout.addLayout(box, 0, 0)

        container, self.fates_from_primogems = display_widget(fates_icon())
        groupbox_layout.addLayout(container, 0, 1)

        box = left_aligned_layout("From", starglitter_icon(), TEXT.STARGLITTER)
        groupbox_layout.addLayout(box, 1, 0)

        container, self.fates_from_starglitter = display_widget(fates_icon())
        groupbox_layout.addLayout(container, 1, 1)

        box = left_aligned_layout("From", fates_icon(), TEXT.FATES)
        groupbox_layout.addLayout(box, 2, 0)

        container, self.fates_from_inventory = display_widget(fates_icon())
        groupbox_layout.addLayout(container, 2, 1)

        box = left_aligned_layout("From", crystal_icon(), TEXT.CRYSTAL)
        groupbox_layout.addLayout(box, 3, 0)
        container, self.fates_from_crystal = display_widget(fates_icon())
        groupbox_layout.addLayout(container, 3, 1)

        box = left_aligned_layout("<b>Total Fates</b>")
        groupbox_layout.addLayout(box, 4, 0)

        container, self.total_fates = display_widget(fates_icon())
        groupbox_layout.addLayout(container, 4, 1)

        self.chart = QChart()

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.chart_view.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.chart_view)

        # from 70 to 90
        self.pity_breakpoints = list(range(70, 91, 5))
        self.pity_count_per_breakpoint = [0 for _ in self.pity_breakpoints]

        chart = QChart()
        chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        # chart.setTitle("Pity Chart")

        self.bar_set = QBarSet("Pity Count")
        self.bar_set.append(self.pity_count_per_breakpoint)

        bar_series = QBarSeries()
        bar_series.append(self.bar_set)

        chart.addSeries(bar_series)

        axis_x = QBarCategoryAxis()
        axis_x.append([str(i) for i in self.pity_breakpoints])
        axis_x.setTitleText("Pity Breakpoints")
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        bar_series.attachAxis(axis_x)

        self.axis_y = QValueAxis()
        max_int_ceil = int(max(self.pity_count_per_breakpoint)) + 2
        min_int_floor = max(int(min(self.pity_count_per_breakpoint)) - 1, 0)
        self.axis_y.setRange(min_int_floor, max_int_ceil)
        self.axis_y.setTickCount(max_int_ceil - min_int_floor + 1)
        self.axis_y.setTitleText("Pity Count")

        chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)
        bar_series.attachAxis(self.axis_y)

        # Hide legend
        chart.legend().setVisible(False)
        chart.setPlotArea(QRectF(60, 10, 300, 190))

        bar_series.setLabelsVisible(True)
        bar_series.setLabelsFormat("@value")
        bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.chart_view.setChart(chart)
        self.chart_view.show()

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

        current_dir = os.getcwd()
        starting_dir = os.path.join(current_dir, CONFIG.SAVE_PATH)
        # Check if directory exists
        if not os.path.exists(starting_dir):
            # Create the directory
            os.makedirs(starting_dir)
        open_dir, _ = QFileDialog.getOpenFileName(
            self, "Open File", starting_dir, "JSON Files (*.json)")
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
            ErrorDialog("Failed to load data from file.")

    def save_data(self):
        """Open a file dialog to save data to a JSON file."""

        current_dir = os.getcwd()
        starting_dir = os.path.join(current_dir, CONFIG.SAVE_PATH)
        # Check if directory exists
        if not os.path.exists(starting_dir):
            # Create the directory
            os.makedirs(starting_dir)
        save_dir, _ = QFileDialog.getSaveFileName(
            self, "Save File", starting_dir, "JSON Files (*.json)")
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

        # If dir does not exist, create it
        save_path = os.path.join(os.getcwd(), CONFIG.SAVE_PATH)
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        save_file = os.path.join(os.getcwd(), CONFIG.SAVE_PATH, 'last_save.json')

        # If file does not exist, create it
        if not os.path.exists(save_file):
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

        save_file = os.path.join(os.getcwd(), CONFIG.SAVE_PATH, 'last_save.json')
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
        self.total_fates.setText(f"<b>{total_fates}</b>")

        # Generate the pity chart
        self.pity_count_per_breakpoint = [round(total_fates / i, 2) for i in self.pity_breakpoints]

        for i, value in enumerate(self.pity_count_per_breakpoint):
            self.bar_set.replace(i, value)

        max_int_ceil = int(max(self.pity_count_per_breakpoint)) + 2
        min_int_floor = max(int(min(self.pity_count_per_breakpoint)) - 1, 0)
        self.axis_y.setRange(min_int_floor, max_int_ceil)
        self.axis_y.setTickCount(max_int_ceil - min_int_floor + 1)

        self.save_to_last_save()

    def simulate(self):
        """Simulate pulls based on the available fates."""

        pulls = self.total_fates.text()
        pulls = int(pulls.replace("<b>", "").replace("</b>", ""))
        dialog = SimulationDialog(self, pulls)

        dialog.exec()
