# test_main_window.py
import pytest
from PySide6.QtWidgets import QApplication
from test_file import MainWindow

@pytest.fixture(scope="session")
def app():
    return QApplication([])

def test_button_click(app):
    window = MainWindow()
    window.show()

    # Simulate a button click
    window.button.click()

    # Check if the button click updated the state
    assert isinstance(window.clicked,list)
    assert window.clicked[1] ==2
    assert window.clicked == [1,2,0,4]
