from PyQt6.QtCharts import (
    QChartView,
    QChart,
    QBarSet,
    QBarSeries,
    QBarCategoryAxis,
    QValueAxis,
)
from PyQt6.QtGui import (
    QPainter,
)
from PyQt6.QtCore import (
    Qt,
    QRectF,
)

from core.text import TEXT


class BarGraph(QChartView):

    def __init__(
            self,
            parent=None,
            geometry: tuple[int, int, int, int] = None,
            title: str = "",
            x_label: str = "",
            x_values: list[str] = None,
            y_label: str = "",
            y_range: tuple[float, float] = (0, 125),
            y_tick_count: int = 6,
            ) -> None:

        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setContentsMargins(0, 0, 0, 0)

        chart = QChart()
        chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.legend().setVisible(False)
        # Setting the following line causes the background to disappear
        # and hides the title as well.
        # There is a also a weird bug where if this is not set,
        # the chart can never be changed again after it is run once,
        # even when changes are made to it in code.
        # We will have to make do with no titles for now.
        chart.setPlotArea(QRectF(*geometry)) if geometry else None
        chart.setBackgroundVisible(False)
        chart.setTitle(title)

        bar_set = QBarSet(title)

        self._bar_set = bar_set

        bar_series = QBarSeries()
        bar_series.append(bar_set)
        bar_series.setLabelsVisible(True)
        bar_series.setLabelsFormat("@value")
        bar_series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)
        bar_series.setBarWidth(1)

        chart.addSeries(bar_series)

        self._bar_series = bar_series

        x_axis = QBarCategoryAxis()
        x_axis.setTitleText(x_label)
        x_axis.append(x_values or [TEXT.BLANK])

        self._x_axis = x_axis

        chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)

        bar_series.attachAxis(x_axis)

        y_axis = QValueAxis()
        y_axis.setTitleText(y_label)
        y_axis.setRange(*y_range)
        y_axis.setTickCount(y_tick_count)

        self._y_axis = y_axis

        chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)

        bar_series.attachAxis(y_axis)

        self.setChart(chart)

    def wheelEvent(self, event) -> None:
        # Disable mouse wheel scrolling because it moves
        # the graph up and down for some reason.
        event.ignore()

    def setAnimationDuration(
            self,
            duration: int
            ) -> None:

        self.chart().setAnimationDuration(duration)

    def clear(self) -> None:

        self._bar_set.remove(0, self._bar_set.count())
        self._x_axis.clear()
        self._x_axis.append([TEXT.BLANK])

    def update_data(
            self,
            data: dict[int, float]
            ) -> None:

        # Note: data must come already sorted in the correct order.
        # Let the Rust backend handle the sorting.

        has_more_data = len(data) > self._bar_set.count()

        # If there are more data points than current bars,
        # add more bars.
        while self._bar_set.count() < len(data):
            self._bar_set.append(0)

        for i, value in enumerate(data.values()):
            self._bar_set.replace(i, value)

        if has_more_data:
            old_x_values = self._x_axis.categories()
            new_x_values = data.keys()

            for i, new_x in enumerate(new_x_values):
                if i < len(old_x_values):
                    self._x_axis.replace(old_x_values[i], str(new_x))
                else:
                    self._x_axis.append(str(new_x))
