import pytest 
from unittest.mock import MagicMock
from PySide6.QtCore import QByteArray
from bluetooth import bluetooth

@pytest.fixture
def bt_instance():
    bt = bluetooth()
    bt.bl_x = [1,2,3]
    bt.bl_y = [0,1,2]
    # Create a mock serial port
    mock_serial = MagicMock()
    
    # Simulate readAll() returning 2 integers: 1 and 2 (little-endian)
    mock_serial.readAll.return_value = QByteArray(b'\x01\x00\x00\x00\x02\x00\x00\x00')
    
    bt.serial  = mock_serial
    return bt

def test_handle_data_received( bt_instance, capsys):
    bt = bt_instance

    # Call the handler directly
    bt.handle_data_received()

    # Capture printed output
    captured = capsys.readouterr()

    # Check expected output
    assert "ketriger" in captured.out
    assert bt.bl_x == [1,2,3,1,2] 
    assert bt.bl_y == [0,1,2,3,4]
    #assert "[1, 2]" in captured.out