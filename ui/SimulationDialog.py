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
    QFrame,
)
from PyQt6.QtGui import (
    QIcon,
    QColor,
)
from PyQt6.QtCore import (
    Qt,
    QTimer,
)

from core.config import CONFIG
from core.assets import ASSETS
from core.text import TEXT
from core.utils import norm_dict, convert_dict
from gachamodel import (
    GenshinImpactGachaModel,
    CapturingRadianceModel,
    SimulationThread,
    SimulationResult,
)
from .utils import (
    set_titlebar_darkmode,
    cmap,
    left_aligned_layout,
)

from .CountSpinbox import CountSpinbox
from .Dropdown import Dropdown
from .BooleanComboBox import BooleanComboBox
from .FrameBox import FrameBox
from .BarGraph import BarGraph


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

        self.model: GenshinImpactGachaModel = None
        self.sim_thread: SimulationThread = None
        self.sim_result: SimulationResult = None

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
        self.sim_length.setRange(1000, 2147483647)
        self.sim_length.setValue(1000000)
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
        self.animation_interval.setRange(50, 900)
        self.animation_interval.setValue(50)
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
        marginal_pmf_tab = QWidget()
        joint_pmf_tab = QWidget()

        # Add tabs to tab widget
        self.tab_widget.addTab(marginal_pmf_tab, TEXT.MARGINAL_PMF)
        self.tab_widget.addTab(joint_pmf_tab, TEXT.JOINT_PMF)

        # Set up Marginal PMF tab with charts
        marginal_pmf_layout = QVBoxLayout()

        # Chart View selector
        self.chart_view_dropdown = Dropdown(options=TEXT.CHART_VIEW_OPTIONS, width=100)
        self.chart_view_dropdown.currentIndexChanged.connect(self.update_charts)
        marginal_pmf_layout.addLayout(left_aligned_layout(TEXT.CHART_VIEW, self.chart_view_dropdown))

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        marginal_pmf_layout.addWidget(line)

        # Featured Chart

        self._featured_chart = BarGraph(
            title=TEXT.FEATURED_5_STAR,
            x_label=TEXT.NUMBER_OF_5_STAR,
            y_label=TEXT.PROBABILITY,
            geometry=CONFIG.CHART.GEOMETRY,
        )
        marginal_pmf_layout.addWidget(self._featured_chart)

        # Standard Chart

        self._standard_chart = BarGraph(
            title=TEXT.STANDARD_5_STAR,
            x_label=TEXT.STANDARD_5_STAR,
            y_label=TEXT.PROBABILITY,
            geometry=CONFIG.CHART.GEOMETRY,
        )
        marginal_pmf_layout.addWidget(self._standard_chart)

        # Combined Chart

        self._combined_chart = BarGraph(
            title=TEXT.TOTAL_5_STAR,
            x_label=TEXT.TOTAL_5_STAR,
            y_label=TEXT.PROBABILITY,
            geometry=CONFIG.CHART.GEOMETRY,
        )
        marginal_pmf_layout.addWidget(self._combined_chart)

        marginal_pmf_tab.setLayout(marginal_pmf_layout)

        # Joint Probability Tab
        joint_layout = QVBoxLayout()
        self.joint_table = QTableWidget()
        self.joint_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.joint_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.joint_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        joint_layout.addWidget(self.joint_table)
        joint_pmf_tab.setLayout(joint_layout)

        # Add tab widget to main layout
        layout.addWidget(self.tab_widget, stretch=1)

        # Set default tab to Marginal PMF
        self.tab_widget.setCurrentIndex(0)

    def start_simulation_thread(self):

        # Get the parameters
        pulls = self.pulls.value()
        pity = self.pity.value()
        guaranteed = self.guaranteed.value()
        cr = self.cr.currentIndex()
        sim_length = self.sim_length.value()
        seed = self.seed.value()
        update_rate = self.animation_interval.value()

        # Set the animation speed
        self._featured_chart.setAnimationDuration(update_rate)
        self._standard_chart.setAnimationDuration(update_rate)
        self._combined_chart.setAnimationDuration(update_rate)

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
            pt=pity,
            g=guaranteed,
            cr_model=CapturingRadianceModel(cr=cr, version=2),
            seed=seed,
        )

        self.info_box.setText(TEXT.SIMULATION_RUNNING)

        # Start the simulation thread (no sleep, runs at max speed)
        self.sim_thread = SimulationThread(self.model, pulls, sim_length)
        self.sim_thread.run()

        # Start the UI update timer
        self.update_timer.setInterval(update_rate)
        self.update_timer.start()

    def stop_simulation_thread(self):

        sim_duration = self.sim_result.sim_duration.total_seconds()
        self.display_elapsed_time(sim_duration)

        self.update_timer.stop()

        # Stop the simulation thread if it's running
        if self.sim_thread and self.sim_thread.is_running():
            self.sim_thread.stop()

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

        # Reset bar sets and axes
        self._featured_chart.clear()
        self._standard_chart.clear()
        self._combined_chart.clear()

        # Reset joint table
        self.joint_table.clear()
        self.joint_table.setRowCount(0)
        self.joint_table.setColumnCount(0)

    def update_ui_from_simulation(self):

        # Get current results from simulation thread
        self.sim_result = self.sim_thread.get_current_results()

        # Update progress bar
        self.progress_bar.setValue(self.sim_result.simulation_count)

        # Check if simulation is complete
        if self.sim_result.simulation_count >= self.sim_length.value():
            self.stop_simulation_thread()

        self.update_charts()
        self.update_joint_table()

    def update_charts(self):

        if not self.sim_result:
            return

        total = self.sim_result.simulation_count
        featured_rolls = self.sim_result.featured_rolls
        standard_rolls = self.sim_result.standard_rolls
        total_rolls = self.sim_result.total_rolls

        mode = TEXT.CHART_VIEW_OPTIONS[self.chart_view_dropdown.currentIndex()]

        # Featured Chart
        featured_converted = convert_dict(featured_rolls, mode)
        self._featured_chart.update_data(norm_dict(featured_converted, total=total))

        # Standard Chart
        standard_converted = convert_dict(standard_rolls, mode)
        self._standard_chart.update_data(norm_dict(standard_converted, total=total))

        # Combined Chart
        combined_converted = convert_dict(total_rolls, mode)
        self._combined_chart.update_data(norm_dict(combined_converted, total=total))

    def update_joint_table(self):
        """Update the joint probability table as a 2D heatmap."""

        joint = self.sim_result.joint_rolls
        if not joint:
            self.joint_table.clear()
            self.joint_table.setRowCount(0)
            self.joint_table.setColumnCount(0)
            return

        # Get sorted unique values for featured and standard
        featured_keys = self.sim_result.featured_rolls.keys()
        standard_keys = self.sim_result.standard_rolls.keys()
        total = self.sim_result.simulation_count

        self.joint_table.setRowCount(len(featured_keys))
        self.joint_table.setColumnCount(len(standard_keys))
        self.joint_table.setHorizontalHeaderLabels([str(s) for s in standard_keys])
        self.joint_table.setVerticalHeaderLabels([str(f) for f in featured_keys])

        # Fill table with probabilities
        for i, f in enumerate(featured_keys):
            for j, s in enumerate(standard_keys):
                prob = (joint.get((f, s), 0) / total * 100) if total > 0 else 0
                text = f"{prob:>8.4f}" if prob > 0 else ""
                item = QTableWidgetItem(text)
                # Make the text larger
                font = item.font()
                font.setPointSize(12)
                item.setFont(font)
                # Make item unselectable
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
                # Color code based on probability
                color = QColor(*cmap(prob / 100))
                item.setBackground(color)
                self.joint_table.setItem(i, j, item)
