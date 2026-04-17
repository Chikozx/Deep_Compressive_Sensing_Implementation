import pyqtgraph as pg
from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
plot_widget = pg.plot()
plot_widget.setWindowTitle('PyQtGraph Plot')

# Set background and title
plot_widget.setBackground('w')
plot_widget.setTitle("My Chart Title", color='k', size='16pt')

# Add axis labels
plot_widget.setLabel('left', 'Y Axis', color='black', size='12pt')
plot_widget.setLabel('bottom', 'X Axis', color='black', size='12pt')

# Add margin
plot_widget.getPlotItem().getViewBox().suggestPadding(2)

# Plot data
x = [0, 1, 2, 3, 4]
y1 = [1, 2, 3, 2, 1]
y2 = [2, 3, 1, 3, 2]

plot_widget.plot(x, y1, pen=pg.mkPen('r', width=2), name='Line 1')
plot_widget.plot(x, y2, pen=pg.mkPen('b', width=2), name='Line 2')

# Add legend
plot_widget.addLegend()

sys.exit(app.exec_())
