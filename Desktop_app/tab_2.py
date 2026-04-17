import numpy as np
import os
from PySide6.QtWidgets import QFileDialog, QWidget, QVBoxLayout, QLabel, QSplitter, QPushButton, QHBoxLayout, QComboBox
from PySide6.QtCharts import QChart, QChartView , QLineSeries 
from PySide6.QtCore import QPointF, QTimer, Qt
import pyqtgraph as pg

from model_obj import model


class tab_2(QWidget):
    def __init__(self):
        super().__init__()
        self.model = model("None")

        #Plot 1 Raw Imported Data
        self.plot_widget_1 = pg.PlotWidget()
        self.plot_widget_1.setBackground('w')
        self.plot = self.plot_widget_1.getPlotItem().plot(pen=pg.mkPen(color='b', width=1))
        self.plot_data_1 = []
        self.plot_widget_1.getPlotItem().setTitle("Imported Signal")

        #Plot 2 Predicted Data
        self.plot_widget_2 = pg.PlotWidget()
        self.plot_widget_2.setBackground('w')
        self.plot_widget_2.getPlotItem().setTitle("Reconstructed Signal")
        self.plot2 = self.plot_widget_2.getPlotItem().plot(pen=pg.mkPen(color='#ff7f0e', width=1))
        self.plot_data_2 = []

        #Plot 3 
        self.plot_widget_3 = pg.PlotWidget()
        self.plot_widget_3.setBackground('w')
        self.plot_widget_3.getPlotItem().setTitle("Real vs Reconstructed Signal")
        
        layout = QVBoxLayout()

        first_button_row = QHBoxLayout()
        
        load_button = QPushButton("Load")
        load_button.setMaximumSize(120,40)
        load_button.clicked.connect(self.load_csv_to_series)


        self.dir = os.path.dirname(os.path.abspath(__file__))
        self.dir = os.path.join(self.dir,"__models")
        self.models = [os.path.splitext(f)[0] for f in os.listdir(self.dir) if f.endswith(".keras") and os.path.isfile(os.path.join(self.dir,f))]

        self.model_select = QComboBox()
        self.model_select.setFixedWidth(150)
        self.model_select.addItem("Select Model")
        self.model_select.addItems(self.models)
        self.model_select.currentTextChanged.connect(self.model_select_funct)
        # self.model_select.currentTextChanged.connect(self.pilihan)

        rec_button = QPushButton("Reconstruct")
        rec_button.setMaximumSize(120,40)
        rec_button.clicked.connect(self.reconstruct_signal)
        

        first_button_row.addStretch()
        first_button_row.addWidget(load_button)
        first_button_row.addWidget(self.model_select)
        first_button_row.addWidget(rec_button)

        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.addWidget(self.plot_widget_1)
        top_splitter.addWidget(self.plot_widget_2)

        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.plot_widget_3)

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

        last_button_row = QHBoxLayout()

        reset_button = QPushButton("Reset")
        reset_button.setMaximumSize(120,40)
        reset_button.clicked.connect(self.reset_button)

        last_button_row.addWidget(reset_button)

        layout.addLayout(first_button_row)
        layout.addWidget(main_splitter)
        layout.addLayout(last_button_row)
        #layout.addWidget(chart_view)
    
        
        self.setLayout(layout)
    
    def load_csv_to_series(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )

        if filename:
            self.plot_data_1 = []
            print(filename)
            y = np.loadtxt(filename, delimiter=',', skiprows=1)
            self.plot_data_1.extend(y[:,1])
            self.plot.setData(self.plot_data_1)
            
            print(f"Loaded data from {filename}")
    
    def model_select_funct(self,text):
        print(text)
        if(text=="Select Model"):
            self.model = model("None")
        else:
            self.model = model(text)
    
    def reset_button(self):
        self.plot_data_1 = []
        self.plot_data_2 = []
        self.plot.clear()
        self.plot2.clear()
        self.plot_widget_3.getPlotItem().clear()


    def reconstruct_signal(self):
        l = int(len(self.plot_data_1)/256)
        rec_buffer = np.array(self.plot_data_1[0:256*l])
        rec_buffer = rec_buffer.reshape((l,256))
        
        #Normalize array
        rec_buffer_min = np.min(rec_buffer,axis=1,keepdims=True)
        rec_buffer_max = np.max(rec_buffer,axis=1,keepdims=True)
        rec_buffer = (rec_buffer - rec_buffer_min)/(rec_buffer_max - rec_buffer_min)

        self.plot_data_2 = []
        if self.model.keras_model.name == "MFFSE":
            rec = self.model.keras_model(rec_buffer)
            for i in range(rec.shape[0]):
                self.plot_data_2.extend(rec[i,:,0])
            rec = np.array(rec).squeeze()
            print(rec.shape)
            self.plot2.setData(self.plot_data_2)
        
        elif self.model.keras_model.name == "TCSSO":
            rec = np.empty((rec_buffer.shape[0],256))
            for i in range(rec_buffer.shape[0]):
                rec[i] = self.model.reconstruct_signal_autoencoder(rec_buffer[i])
            
            print(rec.shape)
            for i in range(rec.shape[0]):
                self.plot_data_2.extend(rec[i])
            self.plot2.setData(self.plot_data_2)
        
        rec = (rec * (rec_buffer_max - rec_buffer_min)) + rec_buffer_min
        print(rec.shape)
        rec = rec.reshape((rec.shape[0]*rec.shape[1]))
        print(rec.shape)
        self.plot_widget_3.getPlotItem().clear()
        self.plot_widget_3.getPlotItem().plot(self.plot_data_1,pen=pg.mkPen(color='b', width=1),name="Real")
        self.plot_widget_3.getPlotItem().plot(rec,pen=pg.mkPen(color='#ff7f0e', width=1),name="Predicted")
