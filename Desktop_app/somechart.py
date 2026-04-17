from PySide6.QtCharts import QChartView
from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt

class ChartWithToggle(QChartView):
    def __init__(self, chart):
        super().__init__(chart)

    
        # Create the buttons
        self.button_pan = QPushButton("Enable Pan", self)
        self.button_pan.setFixedSize(100, 30)
        self.button_pan.move(10, 10)
        self.button_pan.setStyleSheet("background-color: white;")

        self.button_zoom = QPushButton("Enable Zoom", self)
        self.button_zoom.setFixedSize(100, 30)
        self.button_zoom.move(100, 10)  # Adjust position
        self.button_zoom.setStyleSheet("background-color: white;")

        self.button_reset = QPushButton("Reset View", self)
        self.button_reset.setFixedSize(100, 30)
        self.button_reset.move(200, 10)  # Position below other buttons
        self.button_reset.setStyleSheet("background-color: white;")

        # Connect reset button
        self.button_reset.clicked.connect(self.reset_view)

        # Connect the button
        self.button_pan.clicked.connect(self.toggle_pan)
        self.button_zoom.clicked.connect(self.toggle_zoom)

        # Default interactive settings
        self.setRubberBand(QChartView.NoRubberBand)
        self.setDragMode(QChartView.NoDrag)

        # Internal state
        self.pan = False
        self.zoom = False
        self._is_panning = False
        self._last_mouse_pos = None

    def toggle_pan(self):
        if self.pan:
            self.pan = False
            self.setDragMode(QChartView.NoDrag)
            self.button_pan.setText("Enable Pan")
        else:
            self.pan = True
            self.zoom = False
            self.setRubberBand(QChartView.NoRubberBand)
            self.setDragMode(QChartView.ScrollHandDrag)  # We handle panning manually
            self.button_pan.setText("Disable Pan")
            self.button_zoom.setText("Enable Zoom")

    def toggle_zoom(self):
        if self.zoom:
            self.zoom = False
            self.setRubberBand(QChartView.NoRubberBand)
            self.button_zoom.setText("Enable Zoom")
        else:
            self.zoom = True
            self.pan = False
            self.setRubberBand(QChartView.RectangleRubberBand)
            self.setDragMode(QChartView.NoDrag)
            self.button_zoom.setText("Disable Zoom")
            self.button_pan.setText("Enable Pan")

    def reset_view(self):

        axis_y = self.chart().axisY()
        y_val = [point.y() for point in self.chart().series()[0].points()]
        if axis_y:
            axis_y.setRange(min(y_val),max(y_val))
            
        self.chart().zoomReset()  # Reset zoom to full view
        self.chart().scroll(0, 0) # (Optional) Reset scroll if needed
        self.setCursor(Qt.ArrowCursor)  # Reset cursor
        self.setRubberBand(QChartView.NoRubberBand)  # No zoom box
        self.setDragMode(QChartView.NoDrag)  # No hand drag
        self.pan = False
        self.zoom = False
        self.button_pan.setText("Enable Pan")
        self.button_zoom.setText("Enable Zoom")


    def mousePressEvent(self, event):
        if self.pan and event.button() == Qt.LeftButton:
            self._is_panning = True
            self._last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.pan and self._is_panning and event.buttons() & Qt.LeftButton:
            if self._last_mouse_pos is not None:
                delta = event.pos() - self._last_mouse_pos
                if abs(delta.x()) > 1 or abs(delta.y()) > 1:  # Only move if delta is large enough
                    
                    self.chart().scroll(-delta.x(), delta.y())
                    self._last_mouse_pos = event.pos()

                # delta = event.pos() - self._last_mouse_pos
                # self._last_mouse_pos = event.pos()

                # # Move chart while dragging
                # self.chart().scroll(-delta.x(), delta.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.pan and event.button() == Qt.LeftButton:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)