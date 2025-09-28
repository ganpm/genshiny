from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QGridLayout,
    QLabel,
    QProgressBar,
    QTabWidget,
    QWidget,
)
from PyQt6.QtGui import (
    QIcon,
    QPainter,
)
from PyQt6.QtCore import (
    Qt,
    QRectF,
    QThread,
    QObject,
    QTimer,
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
    def __init__(self, model: GIGachaModel, pulls: int, parent: QObject = None):
        super().__init__(parent)
        self.model = model
        self.pulls = pulls
        self._running = True
        self.featured_rolls = {}
        self.standard_rolls = {}
        self.total_rolls = {}
        self.simulation_count = 0

    def run(self):
        while self._running:
            new_featured_rolls, new_standard_rolls = self.model.batch_pull_count(self.pulls)

            # Update internal counts
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

            self.simulation_count += 1

    def stop(self):
        self._running = False

    def get_current_results(self):
        """Thread-safe method to get current simulation results"""
        return (
            self.featured_rolls.copy(),
            self.standard_rolls.copy(),
            self.total_rolls.copy(),
            self.simulation_count
        )


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

        # UI update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_ui_from_simulation)

        self.init_UI(pulls)

    def init_UI(self, pulls):
        layout = QHBoxLayout()

        top_section_layout = QVBoxLayout()

        param_groupbox = QGroupBox()
        param_layout = QGridLayout()

        # Pulls
        self.pulls = CountSpinbox()
        self.pulls.setValue(pulls)
        param_layout.addWidget(QLabel("Pulls"), 0, 0)
        param_layout.addWidget(self.pulls, 0, 1)

        # Pity
        self.pity = CountSpinbox()
        self.pity.setRange(0, 100)
        self.pity.setValue(0)
        param_layout.addWidget(QLabel("Current Pity"), 1, 0)
        param_layout.addWidget(self.pity, 1, 1)

        # Guaranteed
        self.guaranteed = BooleanComboBox(current_index=0, width=120)
        param_layout.addWidget(QLabel("Guaranteed 50/50"), 2, 0)
        param_layout.addWidget(self.guaranteed, 2, 1)

        # Capturing Radiance State
        cr_state = [
            "1 (0% CR)",
            "2 (0% CR)",
            "3 (50% CR)",
            "4 (100% CR)",
        ]
        self.cr = Dropdown(options=cr_state, current_index=0, width=120)
        param_layout.addWidget(QLabel("Capturing Radiance"), 3, 0)
        param_layout.addWidget(self.cr, 3, 1)

        param_groupbox.setLayout(param_layout)
        top_section_layout.addWidget(param_groupbox)

        sim_settings_groupbox = QGroupBox()
        sim_settings_layout = QGridLayout()

        # Simulation Length
        self.sim_length = CountSpinbox()
        self.sim_length.setRange(1000, 1000000)
        self.sim_length.setValue(100000)
        sim_settings_layout.addWidget(QLabel("Simulation Length"), 0, 0)
        sim_settings_layout.addWidget(self.sim_length, 0, 1)

        # Seed
        self.seed = CountSpinbox()
        self.seed.setRange(-2147483648, 2147483647)
        self.seed.setValue(0)
        sim_settings_layout.addWidget(QLabel("Seed"), 1, 0)
        sim_settings_layout.addWidget(self.seed, 1, 1)

        # Animation Interval
        self.animation_interval = CountSpinbox()
        self.animation_interval.setRange(100, 900)
        self.animation_interval.setValue(100)
        # Add a suffix label
        self.animation_interval.setSuffix(" ms")
        sim_settings_layout.addWidget(QLabel("Animation Interval"), 2, 0)
        sim_settings_layout.addWidget(self.animation_interval, 2, 1)

        sim_settings_groupbox.setLayout(sim_settings_layout)
        top_section_layout.addWidget(sim_settings_groupbox)

        layout.addLayout(top_section_layout)

        button_box = QVBoxLayout()

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%v / %m  (%p%)")
        button_box.addWidget(self.progress_bar)

        # Link progress bar range to simulation length
        self.sim_length.valueChanged.connect(
            lambda value: self.progress_bar.setRange(0, value)
        )
        self.progress_bar.setRange(0, self.sim_length.value())

        self.run_button = QPushButton("Run Simulation")
        self.run_button.setFixedHeight(40)
        self.run_button.clicked.connect(self.start_simulation_thread)
        button_box.addWidget(self.run_button)

        self.stop_button = QPushButton("Stop Simulation")
        self.stop_button.setFixedHeight(40)
        self.stop_button.clicked.connect(self.stop_simulation_thread)
        self.stop_button.setEnabled(False)
        button_box.addWidget(self.stop_button)

        self.reset_button = QPushButton("Reset Simulation")
        self.reset_button.setFixedHeight(40)
        self.reset_button.clicked.connect(self.reset_simulation)
        button_box.addWidget(self.reset_button)

        top_section_layout.addLayout(button_box)
        top_section_layout.addStretch(1)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Create tabs
        exact_tab = QWidget()
        at_most_tab = QWidget()
        at_least_tab = QWidget()

        # Add tabs to tab widget
        self.tab_widget.addTab(exact_tab, "Exact")
        self.tab_widget.addTab(at_most_tab, "At Most")
        self.tab_widget.addTab(at_least_tab, "At Least")

        # Set up "Exact" tab with charts
        exact_layout = QVBoxLayout()

        chart_height = 150
        # Featured Character Chart

        self.exact_featured_chart_view = QChartView()
        self.exact_featured_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.exact_featured_chart_view.setContentsMargins(0, 0, 0, 0)
        exact_layout.addWidget(self.exact_featured_chart_view)

        self.exact_featured_chart = QChart()
        self.exact_featured_chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        self.exact_featured_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.exact_featured_chart.setAnimationDuration(100)
        self.exact_featured_chart.legend().setVisible(False)
        self.exact_featured_chart.setPlotArea(QRectF(70, 10, 520, chart_height))

        self.exact_featured_bar_set = QBarSet("Featured 5 Star")

        exact_featured_bar_series = QBarSeries()
        exact_featured_bar_series.append(self.exact_featured_bar_set)
        exact_featured_bar_series.setLabelsVisible(True)
        exact_featured_bar_series.setLabelsFormat("@value")
        exact_featured_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.exact_featured_chart.addSeries(exact_featured_bar_series)

        self.exact_featured_axis_x = QBarCategoryAxis()
        self.exact_featured_axis_x.append(["0"])
        self.exact_featured_axis_x.setTitleText("Number of Featured 5 Stars")
        self.exact_featured_chart.addAxis(self.exact_featured_axis_x, Qt.AlignmentFlag.AlignBottom)
        exact_featured_bar_series.attachAxis(self.exact_featured_axis_x)

        axis_y = QValueAxis()
        max_int_ceil = 100
        min_int_floor = 0
        axis_y.setRange(min_int_floor, max_int_ceil)
        axis_y.setTitleText("Probability (%)")

        self.exact_featured_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        exact_featured_bar_series.attachAxis(axis_y)

        self.exact_featured_chart_view.setChart(self.exact_featured_chart)
        self.exact_featured_chart_view.show()

        # Standard Character Chart

        self.exact_standard_chart_view = QChartView()
        self.exact_standard_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.exact_standard_chart_view.setContentsMargins(0, 0, 0, 0)
        exact_layout.addWidget(self.exact_standard_chart_view)

        self.exact_standard_chart = QChart()
        self.exact_standard_chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        self.exact_standard_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.exact_standard_chart.setAnimationDuration(100)
        self.exact_standard_chart.legend().setVisible(False)
        self.exact_standard_chart.setPlotArea(QRectF(70, 10, 520, chart_height))

        self.exact_standard_bar_set = QBarSet("Standard 5 Star")
        self.exact_standard_bar_set.append(list(self.standard_rolls.values()))

        exact_standard_bar_series = QBarSeries()
        exact_standard_bar_series.append(self.exact_standard_bar_set)
        exact_standard_bar_series.setLabelsVisible(True)
        exact_standard_bar_series.setLabelsFormat("@value")
        exact_standard_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.exact_standard_chart.addSeries(exact_standard_bar_series)

        self.exact_standard_axis_x = QBarCategoryAxis()
        self.exact_standard_axis_x.append(["0"])
        self.exact_standard_axis_x.setTitleText("Number of Standard 5 Stars")
        self.exact_standard_chart.addAxis(self.exact_standard_axis_x, Qt.AlignmentFlag.AlignBottom)
        exact_standard_bar_series.attachAxis(self.exact_standard_axis_x)

        axis_y = QValueAxis()
        max_int_ceil = 100
        min_int_floor = 0
        axis_y.setRange(min_int_floor, max_int_ceil)
        axis_y.setTitleText("Probability (%)")

        self.exact_standard_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        exact_standard_bar_series.attachAxis(axis_y)

        self.exact_standard_chart_view.setChart(self.exact_standard_chart)
        self.exact_standard_chart_view.show()

        # Combined Character Chart

        self.exact_combined_chart_view = QChartView()
        self.exact_combined_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.exact_combined_chart_view.setContentsMargins(0, 0, 0, 0)
        exact_layout.addWidget(self.exact_combined_chart_view)

        self.exact_combined_chart = QChart()
        self.exact_combined_chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        self.exact_combined_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.exact_combined_chart.setAnimationDuration(100)
        self.exact_combined_chart.legend().setVisible(False)
        self.exact_combined_chart.setPlotArea(QRectF(70, 10, 520, chart_height))

        self.exact_combined_bar_set = QBarSet("Total 5 Star")

        exact_combined_bar_series = QBarSeries()
        exact_combined_bar_series.append(self.exact_combined_bar_set)
        exact_combined_bar_series.setLabelsVisible(True)
        exact_combined_bar_series.setLabelsFormat("@value")
        exact_combined_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.exact_combined_chart.addSeries(exact_combined_bar_series)

        self.exact_combined_axis_x = QBarCategoryAxis()
        self.exact_combined_axis_x.append(["0"])
        self.exact_combined_axis_x.setTitleText("Total Number of 5 Stars")
        self.exact_combined_chart.addAxis(self.exact_combined_axis_x, Qt.AlignmentFlag.AlignBottom)
        exact_combined_bar_series.attachAxis(self.exact_combined_axis_x)

        axis_y = QValueAxis()
        max_int_ceil = 100
        min_int_floor = 0
        axis_y.setRange(min_int_floor, max_int_ceil)
        axis_y.setTitleText("Probability (%)")

        self.exact_combined_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        exact_combined_bar_series.attachAxis(axis_y)

        self.exact_combined_chart_view.setChart(self.exact_combined_chart)
        self.exact_combined_chart_view.show()

        exact_layout.addStretch(1)
        exact_tab.setLayout(exact_layout)

        # Add tab widget to main layout
        layout.addWidget(self.tab_widget)

        layout.addStretch(1)
        self.setLayout(layout)

        # Set default tab to "Exact"
        self.tab_widget.setCurrentIndex(0)

    def start_simulation_thread(self):
        # Get the parameters
        pulls = self.pulls.value()
        pity = self.pity.value()
        guaranteed = self.guaranteed.value()
        cr = self.cr.currentIndex()
        seed = self.seed.value()
        update_rate = self.animation_interval.value()

        # Set the animation speed
        self.exact_featured_chart.setAnimationDuration(update_rate)
        self.exact_standard_chart.setAnimationDuration(update_rate)
        self.exact_combined_chart.setAnimationDuration(update_rate)

        # Disable the parameters while simulating
        self.pulls.setEnabled(False)
        self.pity.setEnabled(False)
        self.guaranteed.setEnabled(False)
        self.cr.setEnabled(False)
        self.seed.setEnabled(False)
        self.sim_length.setEnabled(False)
        self.animation_interval.setEnabled(False)

        # Disable the run and reset buttons, enable the stop button
        self.run_button.setEnabled(False)
        self.reset_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # Initialize the model if not already done
        if self.model is None:
            self.model = GIGachaModel(pity, cr, seed, guaranteed)

        # Start the simulation thread (no sleep, runs at max speed)
        self.sim_thread = SimulationThread(self.model, pulls)
        self.sim_thread.start()

        # Start the UI update timer
        self.update_timer.setInterval(update_rate)
        self.update_timer.start()

    def stop_simulation_thread(self):
        # Stop the UI update timer
        self.update_timer.stop()

        # Stop the simulation thread if it's running
        if self.sim_thread and self.sim_thread.isRunning():
            self.sim_thread.stop()
            self.sim_thread.wait()

        # Enable the run and reset buttons, disable the stop button
        self.reset_button.setEnabled(True)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def reset_simulation(self):
        # Stop any running simulation first
        if self.update_timer.isActive():
            self.update_timer.stop()

        if self.sim_thread and self.sim_thread.isRunning():
            self.sim_thread.stop()
            self.sim_thread.wait()

        # Reset progress bar to initial state
        self.progress_bar.setValue(0)
        sim_length = self.sim_length.value()
        self.progress_bar.setRange(0, sim_length)

        # Re-enable all parameters
        self.pulls.setEnabled(True)
        self.pity.setEnabled(True)
        self.guaranteed.setEnabled(True)
        self.cr.setEnabled(True)
        self.seed.setEnabled(True)
        self.sim_length.setEnabled(True)
        self.animation_interval.setEnabled(True)

        # Reset the model and charts
        self.model = None
        self.featured_rolls.clear()
        self.standard_rolls.clear()
        self.total_rolls.clear()

        # Reset bar sets and axes
        self.exact_featured_bar_set.remove(0, self.exact_featured_bar_set.count())
        self.exact_featured_axis_x.clear()
        self.exact_featured_axis_x.append(["0"])
        self.exact_standard_bar_set.remove(0, self.exact_standard_bar_set.count())
        self.exact_standard_axis_x.clear()
        self.exact_standard_axis_x.append(["0"])
        self.exact_combined_bar_set.remove(0, self.exact_combined_bar_set.count())
        self.exact_combined_axis_x.clear()
        self.exact_combined_axis_x.append(["0"])

        # Force chart redraw
        self.exact_featured_chart_view.repaint()
        self.exact_standard_chart_view.repaint()
        self.exact_combined_chart_view.repaint()

    def update_ui_from_simulation(self):
        """Called by timer to update UI with latest simulation results"""
        if not self.sim_thread or not self.sim_thread.isRunning():
            return

        # Get current results from simulation thread
        featured_rolls, standard_rolls, total_rolls, simulation_count = self.sim_thread.get_current_results()

        # Update progress bar
        self.progress_bar.setValue(simulation_count)

        # Check if simulation is complete
        if simulation_count >= self.sim_length.value():
            self.stop_simulation_thread()
            # Ensure progress bar is full
            self.progress_bar.setValue(self.sim_length.value())

        # Update local copies
        self.featured_rolls = featured_rolls
        self.standard_rolls = standard_rolls
        self.total_rolls = total_rolls

        # Update charts
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

        while self.exact_featured_bar_set.count() < len(featured_y_values):
            self.exact_featured_bar_set.append(0)
            changed = True

        for i, y in enumerate(featured_y_values):
            self.exact_featured_bar_set.replace(i, y)

        if changed:
            for i, x in zip(self.exact_featured_axis_x.categories(), featured_x_values):
                self.exact_featured_axis_x.replace(i, x)
            for x in featured_x_values[len(self.exact_featured_axis_x.categories()):]:
                self.exact_featured_axis_x.append(x)

        # Update Standard Chart

        total_simulations = sum(self.standard_rolls.values())
        sorted_keys = sorted(self.standard_rolls.keys())
        standard_x_values = [str(key) for key in sorted_keys]
        standard_y_values = [
            round((self.standard_rolls[key] / total_simulations) * 100, 2)
            for key in sorted_keys
        ]

        changed = False

        while self.exact_standard_bar_set.count() < len(standard_y_values):
            self.exact_standard_bar_set.append(0)
            changed = True

        for i, y in enumerate(standard_y_values):
            self.exact_standard_bar_set.replace(i, y)

        if changed:
            for i, x in zip(self.exact_standard_axis_x.categories(), standard_x_values):
                self.exact_standard_axis_x.replace(i, x)
            for x in standard_x_values[len(self.exact_standard_axis_x.categories()):]:
                self.exact_standard_axis_x.append(x)

        # Update Combined Chart

        total_simulations = sum(self.total_rolls.values())
        sorted_keys = sorted(self.total_rolls.keys())
        combined_x_values = [str(key) for key in sorted_keys]
        combined_y_values = [
            round((self.total_rolls[key] / total_simulations) * 100, 2)
            for key in sorted_keys
        ]

        changed = False

        while self.exact_combined_bar_set.count() < len(combined_y_values):
            self.exact_combined_bar_set.append(0)
            changed = True

        for i, y in enumerate(combined_y_values):
            self.exact_combined_bar_set.replace(i, y)
        if changed:
            for i, x in zip(self.exact_combined_axis_x.categories(), combined_x_values):
                self.exact_combined_axis_x.replace(i, x)
            for x in combined_x_values[len(self.exact_combined_axis_x.categories()):]:
                self.exact_combined_axis_x.append(x)

        # Force chart redraw
        self.exact_featured_chart_view.repaint()
        self.exact_standard_chart_view.repaint()
        self.exact_combined_chart_view.repaint()
