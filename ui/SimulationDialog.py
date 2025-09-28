from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    # QLabel,
    QPushButton,
    QSlider,
    QLabel,
    QFormLayout,
)
from PyQt6.QtGui import (
    QIcon,
    QPainter,
)
from PyQt6.QtCore import (
    Qt,
    QRectF,
    QThread,
    pyqtSignal,
    QObject,
)
from PyQt6.QtCharts import (
    QChart,
    QChartView,
    QBarSet,
    QBarSeries,
    QBarCategoryAxis,
    QValueAxis,
)

from core.config import CONFIG
from core.assets import ASSETS
from core.text import TEXT
from core.model import GIGachaModel
from ui.utils import set_titlebar_darkmode

from .CountSpinbox import CountSpinbox
from .Dropdown import Dropdown
from .BooleanComboBox import BooleanComboBox


class SimulationThread(QThread):
    cycle_done = pyqtSignal(int, int)  # featured_rolls, standard_rolls
    speed_changed = pyqtSignal(int)    # ms

    def __init__(self, model: GIGachaModel, pulls: int, speed: int = 100, parent: QObject = None):
        super().__init__(parent)
        self.model = model
        self.pulls = pulls
        self._running = True
        self._speed = speed

    def run(self):
        while self._running:
            new_featured_rolls, new_standard_rolls = self.model.batch_pull_count(self.pulls)
            self.cycle_done.emit(new_featured_rolls, new_standard_rolls)
            self.msleep(self._speed)

    def stop(self):
        self._running = False

    def set_speed(self, ms: int):
        self._speed = ms


class SimulationDialog(QDialog):
    def __init__(self, parent=None, pulls=600):
        super().__init__(parent)
        set_titlebar_darkmode(self)
        self.setWindowTitle(TEXT.SIMULATE)
        self.setWindowIcon(QIcon(ASSETS.APP_ICON))

        # Center the dialog on the screen
        screen = self.screen()
        screen_geometry = screen.geometry()
        self.setGeometry(
            screen_geometry.x() + (screen_geometry.width() - CONFIG.SIM_WIDTH) // 2,
            screen_geometry.y() + (screen_geometry.height() - CONFIG.SIM_HEIGHT) // 2,
            CONFIG.SIM_WIDTH,
            CONFIG.SIM_HEIGHT)
        self.setFixedSize(*CONFIG.SIM_SIZE)

        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        self.model = None
        self.featured_rolls = {}
        self.standard_rolls = {}
        self.total_rolls = {}
        self.sim_thread = None

        self.init_UI(pulls)

    def init_UI(self, pulls):
        # self.pulls = 600
        # self.sim_length = 100000
        # self.seed = 0
        # self.guaranteed = False
        # self.pity = 0
        # self.cr = 0

        layout = QVBoxLayout()

        top_section_layout = QHBoxLayout()

        param_groupbox = QGroupBox()
        param_layout = QFormLayout()

        # Pulls
        self.pulls = CountSpinbox()
        self.pulls.setValue(pulls)
        param_layout.addRow("Pulls", self.pulls)

        # Pity
        self.pity = CountSpinbox()
        self.pity.setRange(0, 100)
        self.pity.setValue(0)
        param_layout.addRow("Current Pity", self.pity)

        # Guaranteed
        self.guaranteed = BooleanComboBox(current_index=0, width=120)
        param_layout.addRow("Guaranteed 50/50", self.guaranteed)

        # Capturing Radiance State
        cr_state = [
            "1 (0% CR)",
            "2 (0% CR)",
            "3 (50% CR)",
            "4 (100% CR)",
        ]
        self.cr = Dropdown(options=cr_state, current_index=0, width=120)
        param_layout.addRow("Capturing Radiance", self.cr)

        param_groupbox.setLayout(param_layout)
        top_section_layout.addWidget(param_groupbox)

        sim_settings_groupbox = QGroupBox()
        sim_settings_layout = QFormLayout()

        # Simulation Length
        self.sim_length = CountSpinbox()
        self.sim_length.setRange(1000, 1000000)
        self.sim_length.setValue(100000)
        sim_settings_layout.addRow("Simulation Length", self.sim_length)

        # Seed
        self.seed = CountSpinbox()
        self.seed.setRange(-2147483648, 2147483647)
        self.seed.setValue(0)
        sim_settings_layout.addRow("Seed", self.seed)

        # Simulation Speed Slider
        speed_hbox = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(20)
        self.speed_slider.setMaximum(300)
        # self.speed_slider.setSingleStep(50)
        # self.speed_slider.setTickInterval(50)
        # self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.speed_slider.setValue(20)
        self.speed_label = QLabel("20 ms")
        self.speed_slider.valueChanged.connect(lambda v: self.speed_label.setText(f"{v} ms"))
        self.speed_slider.valueChanged.connect(self.update_animation_speed)
        speed_hbox.addWidget(self.speed_slider)
        speed_hbox.addWidget(self.speed_label)
        sim_settings_layout.addRow("Simulation Speed", speed_hbox)

        sim_settings_groupbox.setLayout(sim_settings_layout)
        top_section_layout.addWidget(sim_settings_groupbox)

        layout.addLayout(top_section_layout)

        button_hbox = QHBoxLayout()

        self.run_button = QPushButton("Run Simulation")
        self.run_button.setFixedHeight(40)
        self.run_button.clicked.connect(self.start_simulation_thread)
        button_hbox.addWidget(self.run_button)

        self.stop_button = QPushButton("Stop Simulation")
        self.stop_button.setFixedHeight(40)
        self.stop_button.clicked.connect(self.stop_simulation_thread)
        self.stop_button.setEnabled(False)
        button_hbox.addWidget(self.stop_button)

        self.reset_button = QPushButton("Reset Simulation")
        self.reset_button.setFixedHeight(40)
        self.reset_button.clicked.connect(self.reset_simulation)
        button_hbox.addWidget(self.reset_button)

        layout.addLayout(button_hbox)

        chart_height = 150
        # Featured Character Chart

        self.featured_chart_view = QChartView()
        self.featured_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.featured_chart_view.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.featured_chart_view)

        self.featured_chart = QChart()
        self.featured_chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        self.featured_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.featured_chart.setAnimationDuration(100)
        self.featured_chart.legend().setVisible(False)
        self.featured_chart.setPlotArea(QRectF(70, 10, 520, chart_height))

        self.featured_bar_set = QBarSet("Featured 5 Star")

        featured_bar_series = QBarSeries()
        featured_bar_series.append(self.featured_bar_set)
        featured_bar_series.setLabelsVisible(True)
        featured_bar_series.setLabelsFormat("@value")
        featured_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.featured_chart.addSeries(featured_bar_series)

        self.featured_axis_x = QBarCategoryAxis()
        self.featured_axis_x.append(["0"])
        self.featured_axis_x.setTitleText("Number of Featured 5 Stars")
        self.featured_chart.addAxis(self.featured_axis_x, Qt.AlignmentFlag.AlignBottom)
        featured_bar_series.attachAxis(self.featured_axis_x)

        axis_y = QValueAxis()
        max_int_ceil = 100
        min_int_floor = 0
        axis_y.setRange(min_int_floor, max_int_ceil)
        axis_y.setTitleText("Probability (%)")

        self.featured_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        featured_bar_series.attachAxis(axis_y)

        self.featured_chart_view.setChart(self.featured_chart)
        self.featured_chart_view.show()

        # Standard Character Chart

        self.standard_chart_view = QChartView()
        self.standard_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.standard_chart_view.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.standard_chart_view)

        self.standard_chart = QChart()
        self.standard_chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        self.standard_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.standard_chart.setAnimationDuration(100)
        self.standard_chart.legend().setVisible(False)
        self.standard_chart.setPlotArea(QRectF(70, 10, 520, chart_height))

        self.standard_bar_set = QBarSet("Standard 5 Star")
        self.standard_bar_set.append(list(self.standard_rolls.values()))

        standard_bar_series = QBarSeries()
        standard_bar_series.append(self.standard_bar_set)
        standard_bar_series.setLabelsVisible(True)
        standard_bar_series.setLabelsFormat("@value")
        standard_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.standard_chart.addSeries(standard_bar_series)

        self.standard_axis_x = QBarCategoryAxis()
        self.standard_axis_x.append(["0"])
        self.standard_axis_x.setTitleText("Number of Standard 5 Stars")
        self.standard_chart.addAxis(self.standard_axis_x, Qt.AlignmentFlag.AlignBottom)
        standard_bar_series.attachAxis(self.standard_axis_x)

        axis_y = QValueAxis()
        max_int_ceil = 100
        min_int_floor = 0
        axis_y.setRange(min_int_floor, max_int_ceil)
        axis_y.setTitleText("Probability (%)")

        self.standard_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        standard_bar_series.attachAxis(axis_y)

        self.standard_chart_view.setChart(self.standard_chart)
        self.standard_chart_view.show()

        # Combined Character Chart

        self.combined_chart_view = QChartView()
        self.combined_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.combined_chart_view.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.combined_chart_view)

        self.combined_chart = QChart()
        self.combined_chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        self.combined_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.combined_chart.setAnimationDuration(100)
        self.combined_chart.legend().setVisible(False)
        self.combined_chart.setPlotArea(QRectF(70, 10, 520, chart_height))

        self.combined_bar_set = QBarSet("Total 5 Star")

        combined_bar_series = QBarSeries()
        combined_bar_series.append(self.combined_bar_set)
        combined_bar_series.setLabelsVisible(True)
        combined_bar_series.setLabelsFormat("@value")
        combined_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.combined_chart.addSeries(combined_bar_series)

        self.combined_axis_x = QBarCategoryAxis()
        self.combined_axis_x.append(["0"])
        self.combined_axis_x.setTitleText("Total Number of 5 Stars")
        self.combined_chart.addAxis(self.combined_axis_x, Qt.AlignmentFlag.AlignBottom)
        combined_bar_series.attachAxis(self.combined_axis_x)

        axis_y = QValueAxis()
        max_int_ceil = 100
        min_int_floor = 0
        axis_y.setRange(min_int_floor, max_int_ceil)
        axis_y.setTitleText("Probability (%)")

        self.combined_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        combined_bar_series.attachAxis(axis_y)

        self.combined_chart_view.setChart(self.combined_chart)
        self.combined_chart_view.show()

        layout.addStretch(1)
        self.setLayout(layout)

    def update_animation_speed(self, ms: int):
        if hasattr(self, 'sim_thread') and self.sim_thread.isRunning():
            self.sim_thread.set_speed(ms)
            # Change the animation duration of the charts
            self.featured_chart.setAnimationDuration(ms)
            self.standard_chart.setAnimationDuration(ms)

    def start_simulation_thread(self):
        # Get the parameters
        pulls = self.pulls.value()
        pity = self.pity.value()
        guaranteed = self.guaranteed.value()
        cr = self.cr.currentIndex()
        seed = self.seed.value()
        speed = self.speed_slider.value()

        # Disable the parameters while simulating
        self.pulls.setEnabled(False)
        self.pity.setEnabled(False)
        self.guaranteed.setEnabled(False)
        self.cr.setEnabled(False)
        self.seed.setEnabled(False)
        self.sim_length.setEnabled(False)
        # self.speed_slider.setEnabled(False)

        # Disable the run and reset buttons, enable the stop button
        self.run_button.setEnabled(False)
        self.reset_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # Initialize the model if not already done
        if self.model is None:
            self.model = GIGachaModel(pity, cr, seed, guaranteed)

        # Start the simulation thread
        self.sim_thread = SimulationThread(self.model, pulls, speed)
        self.sim_thread.cycle_done.connect(self.handle_simulation_cycle)
        self.sim_thread.start()

    def stop_simulation_thread(self):
        # Stop the simulation thread if it's running
        if self.sim_thread.isRunning():
            self.sim_thread.stop()
            self.sim_thread.wait()
        # Enable the run and reset buttons, disable the stop button
        self.reset_button.setEnabled(True)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def reset_simulation(self):
        # Re-enable all parameters
        self.pulls.setEnabled(True)
        self.pity.setEnabled(True)
        self.guaranteed.setEnabled(True)
        self.cr.setEnabled(True)
        self.seed.setEnabled(True)
        self.sim_length.setEnabled(True)
        # self.speed_slider.setEnabled(True)

        # Reset the model and charts
        self.model = None
        self.featured_rolls.clear()
        self.standard_rolls.clear()
        # Reset bar sets and axes
        self.featured_bar_set.remove(0, self.featured_bar_set.count())
        self.featured_axis_x.clear()
        self.featured_axis_x.append(["0"])
        self.standard_bar_set.remove(0, self.standard_bar_set.count())
        self.standard_axis_x.clear()
        self.standard_axis_x.append(["0"])
        self.total_rolls.clear()
        self.combined_bar_set.remove(0, self.combined_bar_set.count())
        self.combined_axis_x.clear()
        self.combined_axis_x.append(["0"])
        # Force chart redraw
        self.featured_chart_view.repaint()
        self.standard_chart_view.repaint()
        self.combined_chart_view.repaint()

    def handle_simulation_cycle(self, new_featured_rolls, new_standard_rolls):
        if new_featured_rolls in self.featured_rolls:
            self.featured_rolls[new_featured_rolls] += 1
        else:
            self.featured_rolls[new_featured_rolls] = 1

        if new_standard_rolls in self.standard_rolls:
            self.standard_rolls[new_standard_rolls] += 1
        else:
            self.standard_rolls[new_standard_rolls] = 1

        total_rolls = new_featured_rolls + new_standard_rolls
        if total_rolls in self.total_rolls:
            self.total_rolls[total_rolls] += 1
        else:
            self.total_rolls[total_rolls] = 1

        self.update_charts()

    def update_charts(self):

        total_simulations = sum(self.featured_rolls.values())

        # Update Featured Chart

        sorted_keys = sorted(self.featured_rolls.keys())
        featured_x_values = [str(key) for key in sorted_keys]
        featured_y_values = [
            round((self.featured_rolls[key] / total_simulations) * 100, 2)
            for key in sorted_keys
        ]

        changed = False

        while self.featured_bar_set.count() < len(featured_y_values):
            self.featured_bar_set.append(0)
            changed = True

        for i, y in enumerate(featured_y_values):
            self.featured_bar_set.replace(i, y)

        if changed:
            for i, x in zip(self.featured_axis_x.categories(), featured_x_values):
                self.featured_axis_x.replace(i, x)
            for x in featured_x_values[len(self.featured_axis_x.categories()):]:
                self.featured_axis_x.append(x)

        # Update Standard Chart

        total_simulations = sum(self.standard_rolls.values())
        sorted_keys = sorted(self.standard_rolls.keys())
        standard_x_values = [str(key) for key in sorted_keys]
        standard_y_values = [
            round((self.standard_rolls[key] / total_simulations) * 100, 2)
            for key in sorted_keys
        ]

        changed = False

        while self.standard_bar_set.count() < len(standard_y_values):
            self.standard_bar_set.append(0)
            changed = True

        for i, y in enumerate(standard_y_values):
            self.standard_bar_set.replace(i, y)

        if changed:
            for i, x in zip(self.standard_axis_x.categories(), standard_x_values):
                self.standard_axis_x.replace(i, x)
            for x in standard_x_values[len(self.standard_axis_x.categories()):]:
                self.standard_axis_x.append(x)

        # Update Combined Chart

        total_simulations = sum(self.total_rolls.values())
        sorted_keys = sorted(self.total_rolls.keys())
        combined_x_values = [str(key) for key in sorted_keys]
        combined_y_values = [
            round((self.total_rolls[key] / total_simulations) * 100, 2)
            for key in sorted_keys
        ]

        changed = False

        while self.combined_bar_set.count() < len(combined_y_values):
            self.combined_bar_set.append(0)
            changed = True

        for i, y in enumerate(combined_y_values):
            self.combined_bar_set.replace(i, y)
        if changed:
            for i, x in zip(self.combined_axis_x.categories(), combined_x_values):
                self.combined_axis_x.replace(i, x)
            for x in combined_x_values[len(self.combined_axis_x.categories()):]:
                self.combined_axis_x.append(x)

        # Force chart redraw
        self.featured_chart_view.repaint()
        self.standard_chart_view.repaint()
        self.combined_chart_view.repaint()
