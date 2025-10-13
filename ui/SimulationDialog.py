from PyQt6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QGridLayout,
    QLabel,
    QProgressBar,
    QTabWidget,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PyQt6.QtGui import (
    QIcon,
    QPainter,
    QColor,
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
from threading import Lock

from core.config import CONFIG
from core.assets import ASSETS
from core.text import TEXT
from core.model import GIGachaModel
from ui.utils import set_titlebar_darkmode, cmap

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
        self.joint_rolls = {}
        self.simulation_count = 0
        self.lock = Lock()  # For thread-safe access to results

    def run(self):
        while self._running:
            new_featured_rolls, new_standard_rolls = self.model.batch_pull_count(self.pulls)
            with self.lock:
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

                if (new_featured_rolls, new_standard_rolls) in self.joint_rolls:
                    self.joint_rolls[(new_featured_rolls, new_standard_rolls)] += 1
                else:
                    self.joint_rolls[(new_featured_rolls, new_standard_rolls)] = 1

                self.simulation_count += 1

    def stop(self):
        self._running = False

    def get_current_results(self):
        """Thread-safe method to get current simulation results"""
        with self.lock:
            return (
                self.featured_rolls.copy(),
                self.standard_rolls.copy(),
                self.total_rolls.copy(),
                self.joint_rolls.copy(),
                self.simulation_count
            )


class SimulationWindow(QMainWindow):
    def __init__(self, parent=None, pulls=600):
        super().__init__(parent)
        set_titlebar_darkmode(self)
        self.setWindowTitle(TEXT.SIMULATE)
        self.setWindowIcon(QIcon(ASSETS.APP_ICON))

        # Center the dialog on the screen
        # Disable resizing
        self.setFixedSize(*CONFIG.SIM_SIZE)
        screen = self.screen()
        screen_geometry = screen.geometry()
        self.setGeometry(
            screen_geometry.x() + (screen_geometry.width() - CONFIG.SIM_WIDTH) // 2,
            screen_geometry.y() + (screen_geometry.height() - CONFIG.SIM_HEIGHT) // 2,
            CONFIG.SIM_WIDTH,
            CONFIG.SIM_HEIGHT)
        # Disable maximize button
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        self.model = None
        self.featured_rolls = {}
        self.standard_rolls = {}
        self.total_rolls = {}
        self.joint_rolls = {}
        self.sim_thread = None

        # UI update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_ui_from_simulation)

        self.joint_table = None

        self.initUI(pulls)

    def initUI(self, pulls):
        central_widget = QWidget()

        layout = QHBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        top_section_layout = QVBoxLayout()

        title_label = QLabel("<b>Pull Simulator</b>")
        top_section_layout.addWidget(title_label)

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
        joint_tab = QWidget()

        # Add tabs to tab widget
        self.tab_widget.addTab(exact_tab, "Exactly")
        self.tab_widget.addTab(at_most_tab, "At Most")
        self.tab_widget.addTab(at_least_tab, "At Least")
        self.tab_widget.addTab(joint_tab, "Joint Probability Distribution")

        # Set up "Exact" tab with charts
        exact_layout = QVBoxLayout()

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
        self.exact_featured_chart.setPlotArea(QRectF(*CONFIG.CHART.GEOMETRY))

        self.exact_featured_bar_set = QBarSet("Featured 5 Star")

        exact_featured_bar_series = QBarSeries()
        exact_featured_bar_series.append(self.exact_featured_bar_set)
        exact_featured_bar_series.setLabelsVisible(True)
        exact_featured_bar_series.setLabelsFormat("@value")
        exact_featured_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.exact_featured_chart.addSeries(exact_featured_bar_series)

        self.exact_featured_axis_x = QBarCategoryAxis()
        self.exact_featured_axis_x.append(["0"])
        self.exact_featured_axis_x.setTitleText("Exactly X Featured 5 Stars")
        self.exact_featured_chart.addAxis(self.exact_featured_axis_x, Qt.AlignmentFlag.AlignBottom)
        exact_featured_bar_series.attachAxis(self.exact_featured_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
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
        self.exact_standard_chart.setPlotArea(QRectF(*CONFIG.CHART.GEOMETRY))

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
        self.exact_standard_axis_x.setTitleText("Exactly X Standard 5 Stars")
        self.exact_standard_chart.addAxis(self.exact_standard_axis_x, Qt.AlignmentFlag.AlignBottom)
        exact_standard_bar_series.attachAxis(self.exact_standard_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
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
        self.exact_combined_chart.setPlotArea(QRectF(*CONFIG.CHART.GEOMETRY))

        self.exact_combined_bar_set = QBarSet("Total 5 Star")

        exact_combined_bar_series = QBarSeries()
        exact_combined_bar_series.append(self.exact_combined_bar_set)
        exact_combined_bar_series.setLabelsVisible(True)
        exact_combined_bar_series.setLabelsFormat("@value")
        exact_combined_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.exact_combined_chart.addSeries(exact_combined_bar_series)

        self.exact_combined_axis_x = QBarCategoryAxis()
        self.exact_combined_axis_x.append(["0"])
        self.exact_combined_axis_x.setTitleText("Exactly X 5 Stars")
        self.exact_combined_chart.addAxis(self.exact_combined_axis_x, Qt.AlignmentFlag.AlignBottom)
        exact_combined_bar_series.attachAxis(self.exact_combined_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
        axis_y.setTitleText("Probability (%)")

        self.exact_combined_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        exact_combined_bar_series.attachAxis(axis_y)

        self.exact_combined_chart_view.setChart(self.exact_combined_chart)
        self.exact_combined_chart_view.show()

        exact_layout.addStretch(1)
        exact_tab.setLayout(exact_layout)

        # Set up "At Most" tab with charts
        at_most_layout = QVBoxLayout()

        # At Most Featured Character Chart
        self.at_most_featured_chart_view = QChartView()
        self.at_most_featured_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.at_most_featured_chart_view.setContentsMargins(0, 0, 0, 0)
        at_most_layout.addWidget(self.at_most_featured_chart_view)

        self.at_most_featured_chart = QChart()
        self.at_most_featured_chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        self.at_most_featured_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.at_most_featured_chart.setAnimationDuration(100)
        self.at_most_featured_chart.legend().setVisible(False)
        self.at_most_featured_chart.setPlotArea(QRectF(*CONFIG.CHART.GEOMETRY))

        self.at_most_featured_bar_set = QBarSet("Featured 5 Star")

        at_most_featured_bar_series = QBarSeries()
        at_most_featured_bar_series.append(self.at_most_featured_bar_set)
        at_most_featured_bar_series.setLabelsVisible(True)
        at_most_featured_bar_series.setLabelsFormat("@value")
        at_most_featured_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.at_most_featured_chart.addSeries(at_most_featured_bar_series)

        self.at_most_featured_axis_x = QBarCategoryAxis()
        self.at_most_featured_axis_x.append(["0"])
        self.at_most_featured_axis_x.setTitleText("At Most X Featured 5 Stars")
        self.at_most_featured_chart.addAxis(self.at_most_featured_axis_x, Qt.AlignmentFlag.AlignBottom)
        at_most_featured_bar_series.attachAxis(self.at_most_featured_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
        axis_y.setTitleText("Probability (%)")
        self.at_most_featured_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        at_most_featured_bar_series.attachAxis(axis_y)

        self.at_most_featured_chart_view.setChart(self.at_most_featured_chart)

        # At Most Standard Character Chart
        self.at_most_standard_chart_view = QChartView()
        self.at_most_standard_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.at_most_standard_chart_view.setContentsMargins(0, 0, 0, 0)
        at_most_layout.addWidget(self.at_most_standard_chart_view)

        self.at_most_standard_chart = QChart()
        self.at_most_standard_chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        self.at_most_standard_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.at_most_standard_chart.setAnimationDuration(100)
        self.at_most_standard_chart.legend().setVisible(False)
        self.at_most_standard_chart.setPlotArea(QRectF(*CONFIG.CHART.GEOMETRY))

        self.at_most_standard_bar_set = QBarSet("Standard 5 Star")

        at_most_standard_bar_series = QBarSeries()
        at_most_standard_bar_series.append(self.at_most_standard_bar_set)
        at_most_standard_bar_series.setLabelsVisible(True)
        at_most_standard_bar_series.setLabelsFormat("@value")
        at_most_standard_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.at_most_standard_chart.addSeries(at_most_standard_bar_series)

        self.at_most_standard_axis_x = QBarCategoryAxis()
        self.at_most_standard_axis_x.append(["0"])
        self.at_most_standard_axis_x.setTitleText("At Most X Standard 5 Stars")
        self.at_most_standard_chart.addAxis(self.at_most_standard_axis_x, Qt.AlignmentFlag.AlignBottom)
        at_most_standard_bar_series.attachAxis(self.at_most_standard_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
        axis_y.setTitleText("Probability (%)")
        self.at_most_standard_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        at_most_standard_bar_series.attachAxis(axis_y)

        self.at_most_standard_chart_view.setChart(self.at_most_standard_chart)

        # At Most Combined Character Chart
        self.at_most_combined_chart_view = QChartView()
        self.at_most_combined_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.at_most_combined_chart_view.setContentsMargins(0, 0, 0, 0)
        at_most_layout.addWidget(self.at_most_combined_chart_view)

        self.at_most_combined_chart = QChart()
        self.at_most_combined_chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        self.at_most_combined_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.at_most_combined_chart.setAnimationDuration(100)
        self.at_most_combined_chart.legend().setVisible(False)
        self.at_most_combined_chart.setPlotArea(QRectF(*CONFIG.CHART.GEOMETRY))

        self.at_most_combined_bar_set = QBarSet("Total 5 Star")

        at_most_combined_bar_series = QBarSeries()
        at_most_combined_bar_series.append(self.at_most_combined_bar_set)
        at_most_combined_bar_series.setLabelsVisible(True)
        at_most_combined_bar_series.setLabelsFormat("@value")
        at_most_combined_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.at_most_combined_chart.addSeries(at_most_combined_bar_series)

        self.at_most_combined_axis_x = QBarCategoryAxis()
        self.at_most_combined_axis_x.append(["0"])
        self.at_most_combined_axis_x.setTitleText("At Most X 5 Stars")
        self.at_most_combined_chart.addAxis(self.at_most_combined_axis_x, Qt.AlignmentFlag.AlignBottom)
        at_most_combined_bar_series.attachAxis(self.at_most_combined_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
        axis_y.setTitleText("Probability (%)")
        self.at_most_combined_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        at_most_combined_bar_series.attachAxis(axis_y)

        self.at_most_combined_chart_view.setChart(self.at_most_combined_chart)

        at_most_layout.addStretch(1)
        at_most_tab.setLayout(at_most_layout)

        # Set up "At Least" tab with charts
        at_least_layout = QVBoxLayout()

        # At Least Featured Character Chart
        self.at_least_featured_chart_view = QChartView()
        self.at_least_featured_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.at_least_featured_chart_view.setContentsMargins(0, 0, 0, 0)
        at_least_layout.addWidget(self.at_least_featured_chart_view)

        self.at_least_featured_chart = QChart()
        self.at_least_featured_chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        self.at_least_featured_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.at_least_featured_chart.setAnimationDuration(100)
        self.at_least_featured_chart.legend().setVisible(False)
        self.at_least_featured_chart.setPlotArea(QRectF(*CONFIG.CHART.GEOMETRY))

        self.at_least_featured_bar_set = QBarSet("Featured 5 Star")

        at_least_featured_bar_series = QBarSeries()
        at_least_featured_bar_series.append(self.at_least_featured_bar_set)
        at_least_featured_bar_series.setLabelsVisible(True)
        at_least_featured_bar_series.setLabelsFormat("@value")
        at_least_featured_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.at_least_featured_chart.addSeries(at_least_featured_bar_series)

        self.at_least_featured_axis_x = QBarCategoryAxis()
        self.at_least_featured_axis_x.append(["0"])
        self.at_least_featured_axis_x.setTitleText("At Least X Featured 5 Stars")
        self.at_least_featured_chart.addAxis(self.at_least_featured_axis_x, Qt.AlignmentFlag.AlignBottom)
        at_least_featured_bar_series.attachAxis(self.at_least_featured_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
        axis_y.setTitleText("Probability (%)")
        self.at_least_featured_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        at_least_featured_bar_series.attachAxis(axis_y)

        self.at_least_featured_chart_view.setChart(self.at_least_featured_chart)

        # At Least Standard Character Chart
        self.at_least_standard_chart_view = QChartView()
        self.at_least_standard_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.at_least_standard_chart_view.setContentsMargins(0, 0, 0, 0)
        at_least_layout.addWidget(self.at_least_standard_chart_view)

        self.at_least_standard_chart = QChart()
        self.at_least_standard_chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        self.at_least_standard_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.at_least_standard_chart.setAnimationDuration(100)
        self.at_least_standard_chart.legend().setVisible(False)
        self.at_least_standard_chart.setPlotArea(QRectF(*CONFIG.CHART.GEOMETRY))

        self.at_least_standard_bar_set = QBarSet("Standard 5 Star")

        at_least_standard_bar_series = QBarSeries()
        at_least_standard_bar_series.append(self.at_least_standard_bar_set)
        at_least_standard_bar_series.setLabelsVisible(True)
        at_least_standard_bar_series.setLabelsFormat("@value")
        at_least_standard_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.at_least_standard_chart.addSeries(at_least_standard_bar_series)

        self.at_least_standard_axis_x = QBarCategoryAxis()
        self.at_least_standard_axis_x.append(["0"])
        self.at_least_standard_axis_x.setTitleText("At Least X Standard 5 Stars")
        self.at_least_standard_chart.addAxis(self.at_least_standard_axis_x, Qt.AlignmentFlag.AlignBottom)
        at_least_standard_bar_series.attachAxis(self.at_least_standard_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
        axis_y.setTitleText("Probability (%)")
        self.at_least_standard_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        at_least_standard_bar_series.attachAxis(axis_y)

        self.at_least_standard_chart_view.setChart(self.at_least_standard_chart)

        # At Least Combined Character Chart
        self.at_least_combined_chart_view = QChartView()
        self.at_least_combined_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.at_least_combined_chart_view.setContentsMargins(0, 0, 0, 0)
        at_least_layout.addWidget(self.at_least_combined_chart_view)

        self.at_least_combined_chart = QChart()
        self.at_least_combined_chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        self.at_least_combined_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.at_least_combined_chart.setAnimationDuration(100)
        self.at_least_combined_chart.legend().setVisible(False)
        self.at_least_combined_chart.setPlotArea(QRectF(*CONFIG.CHART.GEOMETRY))

        self.at_least_combined_bar_set = QBarSet("Total 5 Star")

        at_least_combined_bar_series = QBarSeries()
        at_least_combined_bar_series.append(self.at_least_combined_bar_set)
        at_least_combined_bar_series.setLabelsVisible(True)
        at_least_combined_bar_series.setLabelsFormat("@value")
        at_least_combined_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.at_least_combined_chart.addSeries(at_least_combined_bar_series)

        self.at_least_combined_axis_x = QBarCategoryAxis()
        self.at_least_combined_axis_x.append(["0"])
        self.at_least_combined_axis_x.setTitleText("At Least X 5 Stars")
        self.at_least_combined_chart.addAxis(self.at_least_combined_axis_x, Qt.AlignmentFlag.AlignBottom)
        at_least_combined_bar_series.attachAxis(self.at_least_combined_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
        axis_y.setTitleText("Probability (%)")
        self.at_least_combined_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        at_least_combined_bar_series.attachAxis(axis_y)

        self.at_least_combined_chart_view.setChart(self.at_least_combined_chart)

        at_least_layout.addStretch(1)
        at_least_tab.setLayout(at_least_layout)

        # Joint Probability Tab
        joint_layout = QVBoxLayout()
        self.joint_table = QTableWidget()
        self.joint_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.joint_table.setRowCount(1)
        self.joint_table.setColumnCount(1)
        self.joint_table.setHorizontalHeaderLabels(["Standard"])
        self.joint_table.setVerticalHeaderLabels(["Featured"])
        self.joint_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.joint_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        joint_layout.addWidget(self.joint_table)
        joint_tab.setLayout(joint_layout)

        # Add tab widget to main layout
        layout.addWidget(self.tab_widget, stretch=1)

        # layout.addStretch(1)

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
        self.at_most_featured_chart.setAnimationDuration(update_rate)
        self.at_most_standard_chart.setAnimationDuration(update_rate)
        self.at_most_combined_chart.setAnimationDuration(update_rate)
        self.at_least_featured_chart.setAnimationDuration(update_rate)
        self.at_least_standard_chart.setAnimationDuration(update_rate)
        self.at_least_combined_chart.setAnimationDuration(update_rate)

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
            self.model = GIGachaModel(
                pt=pity, cr=cr, seed=seed, guaranteed=guaranteed)

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

        # Reset At Most charts
        self.at_most_featured_bar_set.remove(0, self.at_most_featured_bar_set.count())
        self.at_most_featured_axis_x.clear()
        self.at_most_featured_axis_x.append(["0"])
        self.at_most_standard_bar_set.remove(0, self.at_most_standard_bar_set.count())
        self.at_most_standard_axis_x.clear()
        self.at_most_standard_axis_x.append(["0"])
        self.at_most_combined_bar_set.remove(0, self.at_most_combined_bar_set.count())
        self.at_most_combined_axis_x.clear()
        self.at_most_combined_axis_x.append(["0"])

        # Reset At Least charts
        self.at_least_featured_bar_set.remove(0, self.at_least_featured_bar_set.count())
        self.at_least_featured_axis_x.clear()
        self.at_least_featured_axis_x.append(["0"])
        self.at_least_standard_bar_set.remove(0, self.at_least_standard_bar_set.count())
        self.at_least_standard_axis_x.clear()
        self.at_least_standard_axis_x.append(["0"])
        self.at_least_combined_bar_set.remove(0, self.at_least_combined_bar_set.count())
        self.at_least_combined_axis_x.clear()
        self.at_least_combined_axis_x.append(["0"])

        # Reset joint table
        self.joint_table.clear()
        self.joint_table.setRowCount(1)
        self.joint_table.setColumnCount(1)
        self.joint_table.setHorizontalHeaderLabels(["Standard"])
        self.joint_table.setVerticalHeaderLabels(["Featured"])

        # Force chart redraw
        self.exact_featured_chart_view.repaint()
        self.exact_standard_chart_view.repaint()
        self.exact_combined_chart_view.repaint()
        self.at_most_featured_chart_view.repaint()
        self.at_most_standard_chart_view.repaint()
        self.at_most_combined_chart_view.repaint()
        self.at_least_featured_chart_view.repaint()
        self.at_least_standard_chart_view.repaint()
        self.at_least_combined_chart_view.repaint()

    def update_ui_from_simulation(self):
        """Called by timer to update UI with latest simulation results"""
        if not self.sim_thread or not self.sim_thread.isRunning():
            return

        # Get current results from simulation thread
        featured_rolls, standard_rolls, total_rolls, joint_rolls, simulation_count = self.sim_thread.get_current_results()

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
        self.joint_rolls = joint_rolls

        # Update charts
        self.update_charts()
        # Update joint probability table
        self.update_joint_table()

    def update_charts(self):

        total_simulations = sum(self.featured_rolls.values())

        # Update Featured Chart (Exact)

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

        # Update Standard Chart (Exact)

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

        # Update Combined Chart (Exact)

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

        # Update At Most Charts (CDF)
        # Featured At Most
        sorted_keys = sorted(self.featured_rolls.keys())
        featured_cdf_values = []
        cumulative_prob = 0.0
        for key in sorted_keys:
            cumulative_prob += (self.featured_rolls[key] / total_simulations) * 100
            featured_cdf_values.append(round(cumulative_prob, 2))

        featured_x_values = [str(key) for key in sorted_keys]

        changed = False
        while self.at_most_featured_bar_set.count() < len(featured_cdf_values):
            self.at_most_featured_bar_set.append(0)
            changed = True

        for i, y in enumerate(featured_cdf_values):
            self.at_most_featured_bar_set.replace(i, y)

        if changed:
            for i, x in zip(self.at_most_featured_axis_x.categories(), featured_x_values):
                self.at_most_featured_axis_x.replace(i, x)
            for x in featured_x_values[len(self.at_most_featured_axis_x.categories()):]:
                self.at_most_featured_axis_x.append(x)

        # Standard At Most
        sorted_keys = sorted(self.standard_rolls.keys())
        standard_cdf_values = []
        cumulative_prob = 0.0
        for key in sorted_keys:
            cumulative_prob += (self.standard_rolls[key] / total_simulations) * 100
            standard_cdf_values.append(round(cumulative_prob, 2))

        standard_x_values = [str(key) for key in sorted_keys]

        changed = False
        while self.at_most_standard_bar_set.count() < len(standard_cdf_values):
            self.at_most_standard_bar_set.append(0)
            changed = True

        for i, y in enumerate(standard_cdf_values):
            self.at_most_standard_bar_set.replace(i, y)

        if changed:
            for i, x in zip(self.at_most_standard_axis_x.categories(), standard_x_values):
                self.at_most_standard_axis_x.replace(i, x)
            for x in standard_x_values[len(self.at_most_standard_axis_x.categories()):]:
                self.at_most_standard_axis_x.append(x)

        # Combined At Most
        sorted_keys = sorted(self.total_rolls.keys())
        combined_cdf_values = []
        cumulative_prob = 0.0
        for key in sorted_keys:
            cumulative_prob += (self.total_rolls[key] / total_simulations) * 100
            combined_cdf_values.append(round(cumulative_prob, 2))

        combined_x_values = [str(key) for key in sorted_keys]

        changed = False
        while self.at_most_combined_bar_set.count() < len(combined_cdf_values):
            self.at_most_combined_bar_set.append(0)
            changed = True

        for i, y in enumerate(combined_cdf_values):
            self.at_most_combined_bar_set.replace(i, y)

        if changed:
            for i, x in zip(self.at_most_combined_axis_x.categories(), combined_x_values):
                self.at_most_combined_axis_x.replace(i, x)
            for x in combined_x_values[len(self.at_most_combined_axis_x.categories()):]:
                self.at_most_combined_axis_x.append(x)

        # Update At Least Charts (1 - CDF)
        # Featured At Least
        sorted_keys = sorted(self.featured_rolls.keys())
        featured_at_least_values = []
        total_prob = 100.0
        for i, key in enumerate(sorted_keys):
            if i > 0:
                total_prob -= (self.featured_rolls[sorted_keys[i-1]] / total_simulations) * 100
            featured_at_least_values.append(round(total_prob, 2))

        featured_x_values = [str(key) for key in sorted_keys]

        changed = False
        while self.at_least_featured_bar_set.count() < len(featured_at_least_values):
            self.at_least_featured_bar_set.append(0)
            changed = True

        for i, y in enumerate(featured_at_least_values):
            self.at_least_featured_bar_set.replace(i, y)

        if changed:
            for i, x in zip(self.at_least_featured_axis_x.categories(), featured_x_values):
                self.at_least_featured_axis_x.replace(i, x)
            for x in featured_x_values[len(self.at_least_featured_axis_x.categories()):]:
                self.at_least_featured_axis_x.append(x)

        # Standard At Least
        sorted_keys = sorted(self.standard_rolls.keys())
        standard_at_least_values = []
        total_prob = 100.0
        for i, key in enumerate(sorted_keys):
            if i > 0:
                total_prob -= (self.standard_rolls[sorted_keys[i-1]] / total_simulations) * 100
            standard_at_least_values.append(round(total_prob, 2))

        standard_x_values = [str(key) for key in sorted_keys]

        changed = False
        while self.at_least_standard_bar_set.count() < len(standard_at_least_values):
            self.at_least_standard_bar_set.append(0)
            changed = True

        for i, y in enumerate(standard_at_least_values):
            self.at_least_standard_bar_set.replace(i, y)

        if changed:
            for i, x in zip(self.at_least_standard_axis_x.categories(), standard_x_values):
                self.at_least_standard_axis_x.replace(i, x)
            for x in standard_x_values[len(self.at_least_standard_axis_x.categories()):]:
                self.at_least_standard_axis_x.append(x)

        # Combined At Least
        sorted_keys = sorted(self.total_rolls.keys())
        combined_at_least_values = []
        total_prob = 100.0
        for i, key in enumerate(sorted_keys):
            if i > 0:
                total_prob -= (self.total_rolls[sorted_keys[i-1]] / total_simulations) * 100
            combined_at_least_values.append(round(total_prob, 2))

        combined_x_values = [str(key) for key in sorted_keys]

        changed = False
        while self.at_least_combined_bar_set.count() < len(combined_at_least_values):
            self.at_least_combined_bar_set.append(0)
            changed = True

        for i, y in enumerate(combined_at_least_values):
            self.at_least_combined_bar_set.replace(i, y)

        if changed:
            for i, x in zip(self.at_least_combined_axis_x.categories(), combined_x_values):
                self.at_least_combined_axis_x.replace(i, x)
            for x in combined_x_values[len(self.at_least_combined_axis_x.categories()):]:
                self.at_least_combined_axis_x.append(x)

        # Force chart redraw
        self.exact_featured_chart_view.repaint()
        self.exact_standard_chart_view.repaint()
        self.exact_combined_chart_view.repaint()
        self.at_most_featured_chart_view.repaint()
        self.at_most_standard_chart_view.repaint()
        self.at_most_combined_chart_view.repaint()
        self.at_least_featured_chart_view.repaint()
        self.at_least_standard_chart_view.repaint()
        self.at_least_combined_chart_view.repaint()

    def update_joint_table(self):
        """Update the joint probability table as a 2D heatmap."""
        joint = self.joint_rolls
        if not joint:
            self.joint_table.clear()
            self.joint_table.setRowCount(1)
            self.joint_table.setColumnCount(1)
            self.joint_table.setHorizontalHeaderLabels(["Standard 5★"])
            self.joint_table.setVerticalHeaderLabels(["Featured 5★"])
            return

        # Get sorted unique values for featured and standard
        featured_keys = sorted(set(k[0] for k in joint.keys()))
        standard_keys = sorted(set(k[1] for k in joint.keys()))
        total = sum(joint.values())

        self.joint_table.setRowCount(len(featured_keys))
        self.joint_table.setColumnCount(len(standard_keys))
        self.joint_table.setHorizontalHeaderLabels([str(s) for s in standard_keys])
        self.joint_table.setVerticalHeaderLabels([str(f) for f in featured_keys])

        # Fill table with probabilities
        for i, f in enumerate(featured_keys):
            for j, s in enumerate(standard_keys):
                prob = (joint.get((f, s), 0) / total * 100) if total > 0 else 0
                item = QTableWidgetItem(f"{prob:>8.4f}%")
                # Make the text larger
                font = item.font()
                font.setPointSize(11)
                item.setFont(font)
                # Make item unselectable
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                # Center align the text
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                if prob <= 0:
                    item.setText("")
                # Color code based on probability (sqrt scale + min intensity)
                # color_intensity = int(30 + 215 * (prob / 100) ** 0.5)
                # color = QColor(0, color_intensity, color_intensity)
                color = QColor(*cmap(prob / 100))
                item.setBackground(color)
                self.joint_table.setItem(i, j, item)
