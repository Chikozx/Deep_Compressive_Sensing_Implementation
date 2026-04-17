from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                                 QTextEdit, QLineEdit, QPushButton, QComboBox, QLabel, QFrame,
                                 QGroupBox, QGridLayout)
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtCore import QIODevice, Slot,QObject,Signal
import sys

class SerialMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Serial Monitor")
        self.resize(700, 450)
        self.model = model("None")
        self.model.property_changed.connect(self.update_model_detail)
        self.is_config_transfer = False

        # UI Elements
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet("background-color: #f4f4f4; font-family: Consolas; font-size: 13px;")

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Type message to send...")
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("padding: 6px 12px;")

        self.format_selector = QComboBox()
        self.format_selector.addItems(["UTF-8", "Hex"])

        self.port_selector = QComboBox()
        self.refresh_ports()

        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet("padding: 6px 12px;")

        self.auto_trigger_input = QLineEdit()
        self.auto_trigger_input.setPlaceholderText("Trigger (e.g. M or 0C)")
        self.auto_response_input = QLineEdit()
        self.auto_response_input.setPlaceholderText("Reply (e.g. ACK or 06)")

        self.auto_format_selector = QComboBox()
        self.auto_format_selector.addItems(["UTF-8", "Hex"])

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_lines)

        # Layouts
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Port:"))
        top_layout.addWidget(self.port_selector)
        top_layout.addWidget(self.connect_button)
        top_layout.addSpacing(20)
        top_layout.addWidget(QLabel("Format:"))
        top_layout.addWidget(self.format_selector)
        top_layout.addWidget(self.reset_button)

        auto_layout = QHBoxLayout()
        auto_layout.addWidget(QLabel("Auto Trigger:"))
        auto_layout.addWidget(self.auto_trigger_input)
        auto_layout.addWidget(QLabel("Auto Reply:"))
        auto_layout.addWidget(self.auto_response_input)
        auto_layout.addWidget(self.auto_format_selector)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.input_line)
        bottom_layout.addWidget(self.send_button)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        layout.addWidget(self.output_area)
        layout.addLayout(auto_layout)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator2)

        layout.addLayout(bottom_layout)

        main_layout = QHBoxLayout()

        layout2 = QVBoxLayout()        
        gb = QGroupBox("Details")
        gb_layout = QGridLayout()
        
        self.model_name_label = QLabel(self.model.name)
        self.model_input_label = QLabel(str(self.model.input_size))
        self.model_SM_size_label = QLabel(str(self.model.SM_size))
        self.model_SR_label = QLabel(str(self.model.SR))

        gb_layout.addWidget(QLabel("Model name:"),0,0)
        gb_layout.addWidget(QLabel("Input size:"),1,0)
        gb_layout.addWidget(QLabel("Sensing Matrix size:"),2,0)
        gb_layout.addWidget(QLabel("Sensing Rate:"),3,0)

        gb_layout.addWidget(self.model_name_label,0,1)
        gb_layout.addWidget(self.model_input_label,1,1)
        gb_layout.addWidget(self.model_SM_size_label,2,1)
        gb_layout.addWidget(self.model_SR_label,3,1)
        
        gb.setLayout(gb_layout)
        layout2.addWidget(gb)
        layout2.addStretch()

        main_layout.addLayout(layout)
        main_layout.addLayout(layout2)

        self.setLayout(main_layout)

        # Serial setup
        self.serial = QSerialPort()
        self.serial.readyRead.connect(self.read_data)

        # Connections
        self.connect_button.clicked.connect(self.toggle_connection)
        self.send_button.clicked.connect(self.send_data)

        self.setStyleSheet("QPushButton { background-color: #2e86de; color: white; border: none; border-radius: 4px; } QPushButton:hover { background-color: #1b4f72; }")

    def reset_lines(self):
        self.output_area.clear()

    def refresh_ports(self):
        self.port_selector.clear()
        ports = QSerialPortInfo.availablePorts()
        for port in ports:
            self.port_selector.addItem(port.portName())

    def toggle_connection(self):
        if self.serial.isOpen():
            self.serial.close()
            self.connect_button.setText("Connect")
        else:
            port_name = self.port_selector.currentText()
            self.serial.setPortName(port_name)
            self.serial.setBaudRate(QSerialPort.BaudRate.Baud115200)
            if self.serial.open(QIODevice.ReadWrite):
                self.connect_button.setText("Disconnect")
            else:
                self.output_area.append("Failed to open port")

    @Slot()
    def read_data(self):
        data = self.serial.readAll()
        fmt = self.format_selector.currentText()
        byte_data = bytes(data)

        if self.check_config(byte_data) ==0:
            if fmt == "UTF-8":
                try:
                    text = byte_data.decode("utf-8")
                except UnicodeDecodeError:
                    text = "<Invalid UTF-8 Data>"
            else:  # Hex
                text = ' '.join(f'{b:02X}' for b in byte_data)
            self.output_area.append(text)

            self.check_auto_reply(byte_data)
        

    def send_data(self):
        if self.serial.isOpen():
            text = self.input_line.text().strip()
            if self.format_selector.currentText() == "Hex":
                try:
                    text_clean = text.replace(" ", "")
                    if len(text_clean) % 2 != 0:
                        raise ValueError("Hex input must have an even number of characters")
                    byte_data = bytes.fromhex(text_clean)
                except ValueError as e:
                    self.output_area.append(f"Invalid hex input: {e}")
                    return
            else:
                byte_data = text.encode("utf-8")
            self.serial.write(byte_data)

    def check_auto_reply(self, data: bytes):
        trigger = self.auto_trigger_input.text().strip()
        reply = self.auto_response_input.text().strip()
        reply_fmt = self.auto_format_selector.currentText()

        if not trigger or not reply:
            return

        trigger_bytes = None
        try:
            if reply_fmt == "Hex":
                trigger_clean = trigger.replace(" ", "")
                trigger_bytes = bytes.fromhex(trigger_clean)
            else:
                # Check for comma-separated input like "K,L,M,C"
                if "," in trigger:
                    trigger_list = [item.strip().encode("utf-8") for item in trigger.split(",")]
                    trigger_bytes = tuple(trigger_list)
                else:
                    trigger_bytes = trigger.encode("utf-8")
        except ValueError:
            return

        # Check if trigger matches first or last byte
        if data.startswith(trigger_bytes) or data.endswith(trigger_bytes):
            try:
                if reply_fmt == "Hex":
                    reply_clean = reply.replace(" ", "")
                    if len(reply_clean) % 2 != 0:
                        raise ValueError("Hex reply must have even number of characters")
                    reply_bytes = bytes.fromhex(reply_clean)
                else:
                    reply_bytes = reply.encode("utf-8")
                self.serial.write(reply_bytes)
                self.output_area.append(f"[Auto-reply sent] {reply}")
            except ValueError:
                self.output_area.append("Invalid auto-reply format")
    
    def check_config(self, data: bytes):
        
        if not self.is_config_transfer:
            if data.decode("utf-8", errors='ignore') == "config":
                print(data.decode("utf-8"))
                self.is_config_transfer = True
                self.serial.write("ACK".encode("utf-8"))
                self.output_area.append("Config")
                return 1
            else:
                return 0 

        else:
            if data.startswith("M".encode("utf-8")):
                name = data[2:].decode("utf-8")
                self.model.set_name(name)
                self.output_area.append(f"model_name:{name}")
                self.serial.write("ACK".encode("utf-8"))
                return 1

            elif data.startswith("S".encode("utf-8")):
                print(int.from_bytes(data[2:4],byteorder='little'))
                print(int.from_bytes(data[4:6],byteorder='little'))
                
                self.serial.write("ACK".encode("utf-8"))
                return 1

            elif data.startswith("D".encode("utf-8")):
                print("Data")
                self.serial.write("ACK".encode("utf-8"))
                return 1
            
            elif data.decode("utf-8") == "config_done":
                self.serial.write("ACK".encode("utf-8"))
                self.is_config_transfer = False
                return 1
            
            else:
                return 0
        


    @Slot(str)
    def update_model_detail(self,str):
        if str == "name":
            self.model_name_label.setText(self.model.name)
        elif str == "SM_size":
            self.model_SM_size_label.setText(self.model.SM_size)
            self.model_SR_label.setText(self.model_SR_label)

        


class model(QObject):
    property_changed = Signal(str)
    def __init__(self,name):
        super().__init__()
        self.name = name
        self.input_size = 256
        self.SM_size = None
        self.SR = None
        self.SM = None

    def set_name(self,name):
        self.name = name
        self.property_changed.emit("name")

    def set_SM_size(self,SM_s):
        self.input_size = SM_s
        self.SR = float(SM_s[0]/SM_s[1])
        self.property_changed.emit("SM_size")

    def set_SM(self,SM):
        self.SM = SM




if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SerialMonitor()
    window.show()
    sys.exit(app.exec())
