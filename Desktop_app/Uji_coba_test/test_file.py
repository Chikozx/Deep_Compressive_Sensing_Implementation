# main_window.py
from PySide6.QtWidgets import QMainWindow, QPushButton, QApplication

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test App")
        self.button = QPushButton("Click me")
        self.button.clicked.connect(self.on_click)
        self.setCentralWidget(self.button)
        self.clicked = list()

    def on_click(self):
        self.clicked.extend([1,2,3,4])


if __name__ == "__main__":
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()