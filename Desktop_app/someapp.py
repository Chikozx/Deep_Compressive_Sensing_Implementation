import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QLabel, QHBoxLayout
from tab_1 import tab_1
from tab_2 import tab_2


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 Qt Charts Line Chart")
        self.setGeometry(100, 100, 800, 600)
        

        self.tabs = QTabWidget()

        self.tab1 = tab_1()
        self.tab2 = tab_2()

        self.tabs.addTab(self.tab1, "Real Data")
        self.tabs.addTab(self.tab2, "Load Data")

        pl_lay = QVBoxLayout()
        pl_lay_2 = QHBoxLayout()
        ado =  QLabel("Placeholder_dulu")
        pl_lay.addLayout(pl_lay_2)

        self.setCentralWidget(self.tabs)

    def closeEvent(self, event):
        self.tab1.stopThread()
        super().closeEvent(event)



if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())