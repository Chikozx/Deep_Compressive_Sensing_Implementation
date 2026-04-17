import numpy as np
from PySide6.QtWidgets import QLineEdit, QComboBox, QWidget, QVBoxLayout, QLabel, QFileDialog, QPushButton, QHBoxLayout, QMessageBox, QGroupBox, QGridLayout, QSizePolicy
from PySide6.QtCore import QThread, QTimer, Qt, Slot
from PySide6.QtSerialPort import QSerialPortInfo
from bluetooth import bluetooth, Data_Prediction_Worker, Data_Prediction_Sanity
from model_obj import model
import pyqtgraph as pg
from config import UI_ONLY
from config_popup import ConfigPopup

class tab_1(QWidget):
    def __init__(self):
        super().__init__()
        self.bt = bluetooth(self)
        self.model = model("None")
        self.model.modelChanged.connect(self.model_updated)

        if not UI_ONLY:
            #Multi thread dan Data Process Object
            self.process_thread = QThread(self)
            self.prediction_worker = Data_Prediction_Worker(self)
            self.prediction_worker.moveToThread(self.process_thread)

            #Connect the processing Signal and Slot
            self.bt.Data_ready.connect(self.prediction_worker.start_prediction)
            self.bt.Data_ready_no_work.connect(self.setplot)
            self.prediction_worker.Prediction_done.connect(self.print_test)

            #For Sanity Check
            # self.pred_san = Data_Prediction_Sanity()
            # self.pred_san.moveToThread(self.process_thread)
            # self.bt.Data_Ready_all_Encoder.connect(self.pred_san.pred)
            # self.pred_san.Prediction_done.connect(self.setplot_sanity)
            # self.process_thread.finished.connect(self.pred_san.deleteLater)

            # Connect cleaning thread and worker signal and slot
            self.process_thread.finished.connect(self.prediction_worker.deleteLater)
            

            self.process_thread.start()

        #Chart with pyqtgraph
        self.plot_widget = pg.PlotWidget()
        self.plot = self.plot_widget.getPlotItem().plot()
        self.plot.setDownsampling(auto = True, method = 'subsample')
        self.plot_data = []
        
        #first row elements
        self.bl_indicator = IndicatorLight(color="red")
        
        self.configbutton = QPushButton("Configuration")
        self.configbutton.clicked.connect(lambda: ConfigPopup(self).exec())
        self.configbutton.setEnabled(False)

        self.bl_button = QPushButton("Connect Bluetooth")
        self.bl_button.clicked.connect(self.bluetooth_con)
        self.bl_button.setMaximumSize(120, 40)
        
        portinfo = QSerialPortInfo.availablePorts()
        port_name_list = list()
        for pi in portinfo:
            port_name_list.append(pi.portName())

        self.port_select = QComboBox()
        self.port_select.setFixedWidth(100)
        self.port_select.addItem("Select Port")
        self.port_select.addItems(port_name_list)
        self.port_select.currentTextChanged.connect(self.pilihan)

        #Last row button
        self.button_start = QPushButton("Start")
        self.button_start.clicked.connect(self.bluetooth_start)
		
        self.button_stop = QPushButton("Stop")
        self.button_stop.clicked.connect(self.bluetooth_stop)

        self.savebutton = QPushButton("Save to File")
        self.savebutton.clicked.connect(self.save_series_to_file)

        self.resetbutton = QPushButton("Reset")
        self.resetbutton.clicked.connect(self.reset_button)

        self.stepbutton = QPushButton("Start step")
        self.stepbutton.clicked.connect(self.step_button)

        step_label = QLabel("Please set the step length in seconds:")
        self.step_len = QLineEdit()
        self.step_len.setPlaceholderText("Seconds (s)")
        self.step_len.setMaximumWidth(75)

        #ALL Layout
        layout_atas = QHBoxLayout()
        layout_atas.addWidget(self.bl_indicator)
        layout_atas.addStretch()
        layout_atas.addWidget(QLabel("Port :"), alignment=Qt.AlignRight)
        layout_atas.addWidget(self.port_select, alignment=Qt.AlignRight)
        layout_atas.addWidget(self.bl_button, alignment= Qt.AlignRight)
        
        layout_mode = QGridLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("No Compression Mode",userData="MO0")
        self.mode_combo.addItem("All encoder",userData="MODD")
        #self.mode_combo.addItem("Compression Mode") <- model is none initialized
        
        self.mode_combo.currentTextChanged.connect(self.mode_changed)
        layout_mode.addWidget(self.mode_combo,0,0)

        layout_model_used = QHBoxLayout()
        mu_label = QLabel("Model used :")
        mu_label.setFixedSize(68,16)
        layout_model_used.addWidget(mu_label)
        self.model_name = QLabel(self.model.name)
        layout_model_used.addWidget(self.model_name)

        layout_mode.addLayout(layout_model_used,0,1)
        layout_mode.addWidget(self.configbutton,0,2)
        layout_mode.setColumnStretch(0,5)
        layout_mode.setColumnStretch(1,4)
        layout_mode.setColumnStretch(2,1)


        self.gb_continous = QGroupBox("Continous")
        layout_continous = QHBoxLayout()
        layout_continous.addWidget(self.button_start)
        layout_continous.addWidget(self.button_stop)
        self.gb_continous.setLayout(layout_continous)
        self.gb_continous.setEnabled(False)

        self.gb_step = QGroupBox("Step")
        layout_step = QHBoxLayout()
        layout_step.addWidget(step_label)
        layout_step.addWidget(self.step_len)
        layout_step.addStretch()
        layout_step.addWidget(self.stepbutton)
        self.gb_step.setLayout(layout_step)
        self.gb_step.setEnabled(False)

        layout_con_step = QHBoxLayout()
        layout_con_step.addWidget(self.gb_continous)
        layout_con_step.addWidget(self.gb_step)

        layout_save_reset = QHBoxLayout()
        layout_save_reset.addWidget(self.savebutton)
        layout_save_reset.addWidget(self.resetbutton)

        Central_Layout = QVBoxLayout()
        Central_Layout.addLayout(layout_atas)
        Central_Layout.addWidget(self.plot_widget)
        Central_Layout.addLayout(layout_mode)
        Central_Layout.addLayout(layout_con_step)
        Central_Layout.addLayout(layout_save_reset)
    
        self.setLayout(Central_Layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.updating = False


    #For Sanity Check
    @Slot(object)
    def setplot_sanity(self,data):
        print("Setplot sanity")
        for i in range(data.shape[0]):
            self.plot_data.extend(data[i,:,0])
        print(f"len of plot data :{len(self.plot_data)}")
        self.plot.setData(self.plot_data)

    @Slot(object)
    def setplot(self,data):
        self.plot_data.extend(data)
        self.plot.setData(self.plot_data)
        if len(self.plot_data) > 1024:
            self.plot_widget.getPlotItem().setXRange(len(self.plot_data)-1024,len(self.plot_data))

    @Slot()
    def model_updated(self):
        self.model_name.setText(self.model.name)
        if (self.model.name != "None"):
            if self.mode_combo.findData("MO1")==-1:
                self.mode_combo.addItem("Compression Mode","MO1")
        else:
            if self.mode_combo.findData("MO1")!=-1:
                self.mode_combo.removeItem(1)


    @Slot(str)
    def mode_changed(self,mode):
        print(mode)
        if mode == "Compression Mode":
            self.gb_continous.setEnabled(False)
        elif mode == "No Compression Mode":
            self.gb_continous.setEnabled(True)

    @Slot(object)
    def print_test(self,data):
        #print("From Tab")
        # print(data[0,:,0])
        for i in range(data.shape[0]):
            self.plot_data.extend(data[i])
        print(len(self.plot_data))
        self.plot.setData(self.plot_data)

    def step_button(self):
        len = self.step_len.text()
        try:
            len=float(len)
            if len>180 or len<=0:
                QMessageBox.critical(self,"Please set valid value", "Valid length value is bigger than 0 sec and lesser than 180 sec (3 minutes)")
            else:
                self.bt.bt_step(len,self.mode_combo.currentData())
        except:
            QMessageBox.critical(self,"Please set valid value", "Length can't contain any alphabet and semicolon (use . for decimal point) ")

        
    def reset_button(self):
        # self.bt.bl_x.clear()
        self.plot_data.clear()
        self.plot.setData()
        self.plot_widget.getPlotItem().setXRange(0,1000)
        self.plot_widget.getPlotItem().setYRange(0,5000)

    def save_series_to_file(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Series", "", "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            with open(filename, 'w') as file:
                file.write("x,y\n")  # CSV header
                for point in zip(list(range(len(self.plot_data))), self.plot_data):
                    file.write(f"{point[0]},{point[1]}\n")
            print(f"QLineSeries saved to {filename}")

    def pilihan(self,text):
        print(text)
        self.bt.set_port(text)

    def bluetooth_start(self):
        if not UI_ONLY:
            self.bt.bt_start()
        else:
            print(self.mode_combo.currentText())
	
    def bluetooth_stop(self):
        self.bt.bt_stop()
            
    def bluetooth_con(self):
        if self.bt.is_connected:
            self.bt.bt_dissconnect()
            self.bl_button.setText("Connect Bluetooth")
            self.configbutton.setEnabled(False)
        else:
            self.bt.bt_connect()
            self.bl_button.setText("Disconnect Bluetooth")
            self.configbutton.setEnabled(True)
            self.gb_continous.setEnabled(True)
            self.gb_step.setEnabled(True)
        
        self.bl_indicator.set_color('blue' if self.bt.is_connected else 'red')
        self.bl_button.setText("Disconnect Bluetooth" if self.bt.is_connected else 'Connect Bluetooth')
    
    def stopThread(self):
        if not UI_ONLY:
            self.process_thread.quit()
            self.process_thread.wait()

class IndicatorLight(QLabel):
    def __init__(self, color="gray", diameter=30):
        super().__init__()
        self.diameter = diameter
        self.setFixedSize(diameter, diameter)
        self.set_color(color)

    def set_color(self, color):
        self.setStyleSheet(f"""
            background-color: {color};
            border-radius: {self.diameter // 2}px;
            border: 1.5px solid black;
        """)

