from PyQt6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
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
from timeit import default_timer as timer

from core.config import CONFIG
from core.assets import ASSETS
from core.text import TEXT
from core.modelv2 import GenshinImpactGachaModel
from .utils import set_titlebar_darkmode, cmap

from .CountSpinbox import CountSpinbox
from .Dropdown import Dropdown
from .BooleanComboBox import BooleanComboBox
from .FrameBox import FrameBox


class SimulationThread(QThread):

    def __init__(self, model: GenshinImpactGachaModel, pulls: int, parent: QObject = None):

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
        self.setFixedSize(*CONFIG.SIMULATION.SIZE)
        screen = self.screen()
        screen_geometry = screen.geometry()
        self.setGeometry(
            screen_geometry.x() + (screen_geometry.width() - CONFIG.SIMULATION.SIZE.WIDTH) // 2,
            screen_geometry.y() + (screen_geometry.height() - CONFIG.SIMULATION.SIZE.HEIGHT) // 2,
            CONFIG.SIMULATION.SIZE.WIDTH,
            CONFIG.SIMULATION.SIZE.HEIGHT)
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

        title_label = QLabel(TEXT.PULL_SIMULATOR)
        title_label_font = title_label.font()
        title_label_font.setBold(True)
        title_label.setFont(title_label_font)
        top_section_layout.addWidget(title_label)

        param_groupbox = FrameBox()
        param_layout = QGridLayout()

        # Pulls
        self.pulls = CountSpinbox()
        self.pulls.setValue(pulls)
        param_layout.addWidget(QLabel(TEXT.PULLS), 0, 0)
        param_layout.addWidget(self.pulls, 0, 1)

        # Pity
        self.pity = CountSpinbox()
        self.pity.setRange(0, 100)
        self.pity.setValue(0)
        param_layout.addWidget(QLabel(TEXT.CURRENT_PITY), 1, 0)
        param_layout.addWidget(self.pity, 1, 1)

        # Guaranteed
        self.guaranteed = BooleanComboBox(current_index=0, width=120)
        param_layout.addWidget(QLabel(TEXT.GUARANTEED_5050), 2, 0)
        param_layout.addWidget(self.guaranteed, 2, 1)

        # Capturing Radiance State
        self.cr = Dropdown(options=TEXT.CR_STATES, current_index=0, width=120)
        param_layout.addWidget(QLabel(TEXT.CAPTURING_RADIANCE), 3, 0)
        param_layout.addWidget(self.cr, 3, 1)

        param_groupbox.setLayout(param_layout)
        top_section_layout.addWidget(param_groupbox)
        layout.addLayout(top_section_layout)

        sim_settings_groupbox = FrameBox()
        sim_settings_layout = QGridLayout()

        # Simulation Length
        self.sim_length = CountSpinbox()
        self.sim_length.setRange(1000, 1000000)
        self.sim_length.setValue(100000)
        sim_settings_layout.addWidget(QLabel(TEXT.SIMULATION_LENGTH), 0, 0)
        sim_settings_layout.addWidget(self.sim_length, 0, 1)

        # Seed
        self.seed = CountSpinbox()
        self.seed.setRange(-2147483648, 2147483647)
        self.seed.setValue(0)
        sim_settings_layout.addWidget(QLabel(TEXT.SEED), 1, 0)
        sim_settings_layout.addWidget(self.seed, 1, 1)

        # Animation Interval
        self.animation_interval = CountSpinbox()
        self.animation_interval.setRange(100, 900)
        self.animation_interval.setValue(100)
        # Add a suffix label
        self.animation_interval.setSuffix(TEXT.ANIMATION_SUFFIX)
        sim_settings_layout.addWidget(QLabel(TEXT.ANIMATION_INTERVAL), 2, 0)
        sim_settings_layout.addWidget(self.animation_interval, 2, 1)

        sim_settings_groupbox.setLayout(sim_settings_layout)
        top_section_layout.addWidget(sim_settings_groupbox)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(TEXT.PROGRESS_BAR_FORMAT)
        top_section_layout.addWidget(self.progress_bar)

        # Link progress bar range to simulation length
        self.sim_length.valueChanged.connect(
            lambda value: self.progress_bar.setRange(0, value)
        )
        self.progress_bar.setRange(0, self.sim_length.value())

        # Simulation Control Buttons
        button_box = QHBoxLayout()

        self.run_button = QPushButton(TEXT.RUN)
        self.run_button.setFixedHeight(40)
        self.run_button.clicked.connect(self.start_simulation_thread)
        button_box.addWidget(self.run_button)

        self.stop_button = QPushButton(TEXT.STOP)
        self.stop_button.setFixedHeight(40)
        self.stop_button.clicked.connect(self.stop_simulation_thread)
        self.stop_button.setEnabled(False)
        button_box.addWidget(self.stop_button)

        self.reset_button = QPushButton(TEXT.RESET)
        self.reset_button.setFixedHeight(40)
        self.reset_button.clicked.connect(self.reset_simulation)
        button_box.addWidget(self.reset_button)

        top_section_layout.addLayout(button_box)

        # Info box
        info_box_frame = FrameBox()
        info_box_layout = QVBoxLayout()
        info_box_frame.setLayout(info_box_layout)

        self.info_box = QLabel()
        self.info_box.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        self.info_box.setWordWrap(True)

        info_box_layout.addWidget(self.info_box)
        top_section_layout.addWidget(info_box_frame)

        top_section_layout.addStretch(1)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Create tabs
        exact_tab = QWidget()
        at_most_tab = QWidget()
        at_least_tab = QWidget()
        joint_tab = QWidget()

        # Add tabs to tab widget
        self.tab_widget.addTab(exact_tab, TEXT.EXACTLY)
        self.tab_widget.addTab(at_most_tab, TEXT.AT_MOST)
        self.tab_widget.addTab(at_least_tab, TEXT.AT_LEAST)
        self.tab_widget.addTab(joint_tab, TEXT.JOINTLY)

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

        self.exact_featured_bar_set = QBarSet(TEXT.FEATURED_5_STAR)

        exact_featured_bar_series = QBarSeries()
        exact_featured_bar_series.append(self.exact_featured_bar_set)
        exact_featured_bar_series.setLabelsVisible(True)
        exact_featured_bar_series.setLabelsFormat("@value")
        exact_featured_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.exact_featured_chart.addSeries(exact_featured_bar_series)

        self.exact_featured_axis_x = QBarCategoryAxis()
        self.exact_featured_axis_x.append([TEXT.BLANK])
        self.exact_featured_axis_x.setTitleText(TEXT.NUMBER_OF_5_STAR)
        self.exact_featured_chart.addAxis(self.exact_featured_axis_x, Qt.AlignmentFlag.AlignBottom)
        exact_featured_bar_series.attachAxis(self.exact_featured_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
        axis_y.setTitleText(TEXT.PROBABILITY)

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

        self.exact_standard_bar_set = QBarSet(TEXT.STANDARD_5_STAR)
        self.exact_standard_bar_set.append(list(self.standard_rolls.values()))

        exact_standard_bar_series = QBarSeries()
        exact_standard_bar_series.append(self.exact_standard_bar_set)
        exact_standard_bar_series.setLabelsVisible(True)
        exact_standard_bar_series.setLabelsFormat("@value")
        exact_standard_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.exact_standard_chart.addSeries(exact_standard_bar_series)

        self.exact_standard_axis_x = QBarCategoryAxis()
        self.exact_standard_axis_x.append([TEXT.BLANK])
        self.exact_standard_axis_x.setTitleText(TEXT.NUMBER_OF_5_STAR)
        self.exact_standard_chart.addAxis(self.exact_standard_axis_x, Qt.AlignmentFlag.AlignBottom)
        exact_standard_bar_series.attachAxis(self.exact_standard_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
        axis_y.setTitleText(TEXT.PROBABILITY)

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

        self.exact_combined_bar_set = QBarSet(TEXT.TOTAL_5_STAR)

        exact_combined_bar_series = QBarSeries()
        exact_combined_bar_series.append(self.exact_combined_bar_set)
        exact_combined_bar_series.setLabelsVisible(True)
        exact_combined_bar_series.setLabelsFormat("@value")
        exact_combined_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.exact_combined_chart.addSeries(exact_combined_bar_series)

        self.exact_combined_axis_x = QBarCategoryAxis()
        self.exact_combined_axis_x.append([TEXT.BLANK])
        self.exact_combined_axis_x.setTitleText(TEXT.NUMBER_OF_5_STAR)
        self.exact_combined_chart.addAxis(self.exact_combined_axis_x, Qt.AlignmentFlag.AlignBottom)
        exact_combined_bar_series.attachAxis(self.exact_combined_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
        axis_y.setTitleText(TEXT.PROBABILITY)

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

        self.at_most_featured_bar_set = QBarSet(TEXT.FEATURED_5_STAR)

        at_most_featured_bar_series = QBarSeries()
        at_most_featured_bar_series.append(self.at_most_featured_bar_set)
        at_most_featured_bar_series.setLabelsVisible(True)
        at_most_featured_bar_series.setLabelsFormat("@value")
        at_most_featured_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.at_most_featured_chart.addSeries(at_most_featured_bar_series)

        self.at_most_featured_axis_x = QBarCategoryAxis()
        self.at_most_featured_axis_x.append([TEXT.BLANK])
        self.at_most_featured_axis_x.setTitleText(TEXT.NUMBER_OF_5_STAR)
        self.at_most_featured_chart.addAxis(self.at_most_featured_axis_x, Qt.AlignmentFlag.AlignBottom)
        at_most_featured_bar_series.attachAxis(self.at_most_featured_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
        axis_y.setTitleText(TEXT.PROBABILITY)

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

        self.at_most_standard_bar_set = QBarSet(TEXT.STANDARD_5_STAR)

        at_most_standard_bar_series = QBarSeries()
        at_most_standard_bar_series.append(self.at_most_standard_bar_set)
        at_most_standard_bar_series.setLabelsVisible(True)
        at_most_standard_bar_series.setLabelsFormat("@value")
        at_most_standard_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.at_most_standard_chart.addSeries(at_most_standard_bar_series)

        self.at_most_standard_axis_x = QBarCategoryAxis()
        self.at_most_standard_axis_x.append([TEXT.BLANK])
        self.at_most_standard_axis_x.setTitleText(TEXT.NUMBER_OF_5_STAR)
        self.at_most_standard_chart.addAxis(self.at_most_standard_axis_x, Qt.AlignmentFlag.AlignBottom)
        at_most_standard_bar_series.attachAxis(self.at_most_standard_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
        axis_y.setTitleText(TEXT.PROBABILITY)
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

        self.at_most_combined_bar_set = QBarSet(TEXT.TOTAL_5_STAR)

        at_most_combined_bar_series = QBarSeries()
        at_most_combined_bar_series.append(self.at_most_combined_bar_set)
        at_most_combined_bar_series.setLabelsVisible(True)
        at_most_combined_bar_series.setLabelsFormat("@value")
        at_most_combined_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.at_most_combined_chart.addSeries(at_most_combined_bar_series)

        self.at_most_combined_axis_x = QBarCategoryAxis()
        self.at_most_combined_axis_x.append([TEXT.BLANK])
        self.at_most_combined_axis_x.setTitleText(TEXT.NUMBER_OF_5_STAR)
        self.at_most_combined_chart.addAxis(self.at_most_combined_axis_x, Qt.AlignmentFlag.AlignBottom)
        at_most_combined_bar_series.attachAxis(self.at_most_combined_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
        axis_y.setTitleText(TEXT.PROBABILITY)

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

        self.at_least_featured_bar_set = QBarSet(TEXT.FEATURED_5_STAR)

        at_least_featured_bar_series = QBarSeries()
        at_least_featured_bar_series.append(self.at_least_featured_bar_set)
        at_least_featured_bar_series.setLabelsVisible(True)
        at_least_featured_bar_series.setLabelsFormat("@value")
        at_least_featured_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.at_least_featured_chart.addSeries(at_least_featured_bar_series)

        self.at_least_featured_axis_x = QBarCategoryAxis()
        self.at_least_featured_axis_x.append([TEXT.BLANK])
        self.at_least_featured_axis_x.setTitleText(TEXT.NUMBER_OF_5_STAR)
        self.at_least_featured_chart.addAxis(self.at_least_featured_axis_x, Qt.AlignmentFlag.AlignBottom)
        at_least_featured_bar_series.attachAxis(self.at_least_featured_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
        axis_y.setTitleText(TEXT.PROBABILITY)

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

        self.at_least_standard_bar_set = QBarSet(TEXT.STANDARD_5_STAR)

        at_least_standard_bar_series = QBarSeries()
        at_least_standard_bar_series.append(self.at_least_standard_bar_set)
        at_least_standard_bar_series.setLabelsVisible(True)
        at_least_standard_bar_series.setLabelsFormat("@value")
        at_least_standard_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.at_least_standard_chart.addSeries(at_least_standard_bar_series)

        self.at_least_standard_axis_x = QBarCategoryAxis()
        self.at_least_standard_axis_x.append([TEXT.BLANK])
        self.at_least_standard_axis_x.setTitleText(TEXT.NUMBER_OF_5_STAR)
        self.at_least_standard_chart.addAxis(self.at_least_standard_axis_x, Qt.AlignmentFlag.AlignBottom)
        at_least_standard_bar_series.attachAxis(self.at_least_standard_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
        axis_y.setTitleText(TEXT.PROBABILITY)

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

        self.at_least_combined_bar_set = QBarSet(TEXT.TOTAL_5_STAR)

        at_least_combined_bar_series = QBarSeries()
        at_least_combined_bar_series.append(self.at_least_combined_bar_set)
        at_least_combined_bar_series.setLabelsVisible(True)
        at_least_combined_bar_series.setLabelsFormat("@value")
        at_least_combined_bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        self.at_least_combined_chart.addSeries(at_least_combined_bar_series)

        self.at_least_combined_axis_x = QBarCategoryAxis()
        self.at_least_combined_axis_x.append([TEXT.BLANK])
        self.at_least_combined_axis_x.setTitleText(TEXT.NUMBER_OF_5_STAR)
        self.at_least_combined_chart.addAxis(self.at_least_combined_axis_x, Qt.AlignmentFlag.AlignBottom)
        at_least_combined_bar_series.attachAxis(self.at_least_combined_axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, 125)
        axis_y.setTickCount(6)
        axis_y.setTitleText(TEXT.PROBABILITY)

        self.at_least_combined_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        at_least_combined_bar_series.attachAxis(axis_y)

        self.at_least_combined_chart_view.setChart(self.at_least_combined_chart)

        at_least_layout.addStretch(1)
        at_least_tab.setLayout(at_least_layout)

        # Joint Probability Tab
        joint_layout = QVBoxLayout()
        self.joint_table = QTableWidget()
        self.joint_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.joint_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.joint_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        joint_layout.addWidget(self.joint_table)
        joint_tab.setLayout(joint_layout)

        # Add tab widget to main layout
        layout.addWidget(self.tab_widget, stretch=1)

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

        # Initialize the model
        self.model = GenshinImpactGachaModel(
            pt=pity, cr=cr, seed=seed, guaranteed=guaranteed)

        # Record the start time
        self.sim_start_time = timer()

        self.info_box.setText(TEXT.SIMULATION_RUNNING)

        # Start the simulation thread (no sleep, runs at max speed)
        self.sim_thread = SimulationThread(self.model, pulls)
        self.sim_thread.start()

        # Start the UI update timer
        self.update_timer.setInterval(update_rate)
        self.update_timer.start()

    def stop_simulation_thread(self):

        # Stop the UI update timer
        self.update_timer.stop()

        # Record the end time
        self.sim_end_time = timer()

        self.display_elapsed_time(self.sim_end_time - self.sim_start_time)

        # Stop the simulation thread if it's running
        if self.sim_thread and self.sim_thread.isRunning():
            self.sim_thread.stop()
            self.sim_thread.wait()

        # Enable the run and reset buttons, disable the stop button
        self.reset_button.setEnabled(True)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def display_elapsed_time(self, seconds: float):
        """Display elapsed time in the info box"""

        m = seconds // 60
        s = seconds % 60
        ms = int((seconds - int(seconds)) * 1000)
        fmt = ""
        if m > 0:
            fmt += f"{int(m)}m "
        fmt += f"{int(s)}.{ms:03d}s"
        self.info_box.setText(TEXT.SIMULATION_COMPLETED.format(fmt))

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

        # Reset info box
        self.info_box.setText(TEXT.BLANK)

        # Reset the model and charts
        self.model = None
        self.featured_rolls.clear()
        self.standard_rolls.clear()
        self.total_rolls.clear()

        # Reset bar sets and axes
        self.exact_featured_bar_set.remove(0, self.exact_featured_bar_set.count())
        self.exact_featured_axis_x.clear()
        self.exact_featured_axis_x.append([TEXT.BLANK])
        self.exact_standard_bar_set.remove(0, self.exact_standard_bar_set.count())
        self.exact_standard_axis_x.clear()
        self.exact_standard_axis_x.append([TEXT.BLANK])
        self.exact_combined_bar_set.remove(0, self.exact_combined_bar_set.count())
        self.exact_combined_axis_x.clear()
        self.exact_combined_axis_x.append([TEXT.BLANK])

        # Reset At Most charts
        self.at_most_featured_bar_set.remove(0, self.at_most_featured_bar_set.count())
        self.at_most_featured_axis_x.clear()
        self.at_most_featured_axis_x.append([TEXT.BLANK])
        self.at_most_standard_bar_set.remove(0, self.at_most_standard_bar_set.count())
        self.at_most_standard_axis_x.clear()
        self.at_most_standard_axis_x.append([TEXT.BLANK])
        self.at_most_combined_bar_set.remove(0, self.at_most_combined_bar_set.count())
        self.at_most_combined_axis_x.clear()
        self.at_most_combined_axis_x.append([TEXT.BLANK])

        # Reset At Least charts
        self.at_least_featured_bar_set.remove(0, self.at_least_featured_bar_set.count())
        self.at_least_featured_axis_x.clear()
        self.at_least_featured_axis_x.append([TEXT.BLANK])
        self.at_least_standard_bar_set.remove(0, self.at_least_standard_bar_set.count())
        self.at_least_standard_axis_x.clear()
        self.at_least_standard_axis_x.append([TEXT.BLANK])
        self.at_least_combined_bar_set.remove(0, self.at_least_combined_bar_set.count())
        self.at_least_combined_axis_x.clear()
        self.at_least_combined_axis_x.append([TEXT.BLANK])

        # Reset joint table
        self.joint_table.clear()
        self.joint_table.setRowCount(0)
        self.joint_table.setColumnCount(0)

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

        # Update Featured Chart (Exact)

        total_simulations = sum(self.featured_rolls.values())
        min_key = min(self.featured_rolls.keys())
        max_key = max(self.featured_rolls.keys())
        featured_keys = list(range(min_key, max_key + 1))
        featured_x_values = [str(key) for key in featured_keys]
        featured_y_values = [
            round((self.featured_rolls.get(key, 0) / total_simulations) * 100, 2)
            for key in featured_keys
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
        min_key = min(self.standard_rolls.keys())
        max_key = max(self.standard_rolls.keys())
        standard_keys = list(range(min_key, max_key + 1))
        standard_x_values = [str(key) for key in standard_keys]
        standard_y_values = [
            round((self.standard_rolls.get(key, 0) / total_simulations) * 100, 2)
            for key in standard_keys
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
        min_key = min(self.total_rolls.keys())
        max_key = max(self.total_rolls.keys())
        combined_keys = list(range(min_key, max_key + 1))
        combined_x_values = [str(key) for key in combined_keys]
        combined_y_values = [
            round((self.total_rolls.get(key, 0) / total_simulations) * 100, 2)
            for key in combined_keys
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

        # Update Featured Chart (At Most)

        featured_cdf_values = []
        cumulative_prob = 0.0
        for key in featured_keys:
            cumulative_prob += (self.featured_rolls.get(key, 0) / total_simulations) * 100
            featured_cdf_values.append(round(cumulative_prob, 2))

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

        # Update Standard Chart (At Most)

        standard_cdf_values = []
        cumulative_prob = 0.0
        for key in standard_keys:
            cumulative_prob += (self.standard_rolls.get(key, 0) / total_simulations) * 100
            standard_cdf_values.append(round(cumulative_prob, 2))

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

        # Update Combined Chart (At Most)

        combined_cdf_values = []
        cumulative_prob = 0.0
        for key in combined_keys:
            cumulative_prob += (self.total_rolls.get(key, 0) / total_simulations) * 100
            combined_cdf_values.append(round(cumulative_prob, 2))

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

        # Update Featured Chart (At Least)

        featured_at_least_values = []
        total_prob = 100.0
        for i, key in enumerate(featured_keys):
            if i > 0:
                total_prob -= (self.featured_rolls.get(featured_keys[i-1], 0) / total_simulations) * 100
            featured_at_least_values.append(round(total_prob, 2))

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

        # Update Standard Chart (At Least)

        standard_at_least_values = []
        total_prob = 100.0
        for i, key in enumerate(standard_keys):
            if i > 0:
                total_prob -= (self.standard_rolls.get(standard_keys[i-1], 0) / total_simulations) * 100
            standard_at_least_values.append(round(total_prob, 2))

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

        # Update Combined Chart (At Least)

        combined_at_least_values = []
        total_prob = 100.0
        for i, key in enumerate(combined_keys):
            if i > 0:
                total_prob -= (self.total_rolls.get(combined_keys[i-1], 0) / total_simulations) * 100
            combined_at_least_values.append(round(total_prob, 2))

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
            self.joint_table.setRowCount(0)
            self.joint_table.setColumnCount(0)
            return

        # Get sorted unique values for featured and standard
        featured_keys = list(range(min(self.featured_rolls.keys()), max(self.featured_rolls.keys()) + 1))
        standard_keys = list(range(min(self.standard_rolls.keys()), max(self.standard_rolls.keys()) + 1))
        total = sum(joint.values())

        self.joint_table.setRowCount(len(featured_keys))
        self.joint_table.setColumnCount(len(standard_keys))
        self.joint_table.setHorizontalHeaderLabels([str(s) for s in standard_keys])
        self.joint_table.setVerticalHeaderLabels([str(f) for f in featured_keys])

        # Fill table with probabilities
        for i, f in enumerate(featured_keys):
            for j, s in enumerate(standard_keys):
                prob = (joint.get((f, s), 0) / total * 100) if total > 0 else 0
                text = f"{prob:>8.4f}%" if prob > 0 else ""
                item = QTableWidgetItem(text)
                # Make the text larger
                font = item.font()
                font.setPointSize(11)
                item.setFont(font)
                # Make item unselectable
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
                # Color code based on probability
                color = QColor(*cmap(prob / 100))
                item.setBackground(color)
                self.joint_table.setItem(i, j, item)
