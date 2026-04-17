import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSplitter
)
from PySide6.QtCharts import QChart, QChartView, QLineSeries
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor


def create_chart(title="Chart"):
    # Create a simple line chart with sample data
    series = QLineSeries()
    for x in range(10):
        series.append(x, x * x % 10)

    # Make the chart line more visible
    pen = QPen(QColor("blue"))
    pen.setWidth(3)
    series.setPen(pen)

    chart = QChart()
    chart.addSeries(series)
    chart.setTitle(title)
    chart.createDefaultAxes()

    chart_view = QChartView(chart)
    return chart_view


class ChartWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Resizable Charts with Styled Splitters")
        self.resize(1000, 600)

        # Create charts
        chart1 = create_chart("Chart 1")
        chart2 = create_chart("Chart 2")
        adc_chart = create_chart("ADC Graph")

        # Top row: two charts side-by-side
        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.addWidget(chart1)
        top_splitter.addWidget(chart2)

        # Main layout: top row and bottom chart (ADC)
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(adc_chart)

        # Make splitter handles thicker and styled
        main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #444;
            }
            QSplitter::handle:horizontal {
                height: 10px;
            }
            QSplitter::handle:vertical {
                width: 10px;
            }
        """)

        # Set main layout
        layout = QVBoxLayout()
        layout.addWidget(main_splitter)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChartWindow()
    window.show()
    sys.exit(app.exec())
