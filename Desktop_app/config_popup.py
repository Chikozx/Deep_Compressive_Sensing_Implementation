import os , shutil
from PySide6.QtWidgets import QMessageBox, QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QFileDialog, QGroupBox, QGridLayout
from config import UI_ONLY
from model_obj import model

class ConfigPopup(QDialog):
    def __init__(self,tab_1):
        super().__init__()
        self.model = tab_1.model
        self.parent = tab_1
        self.setFixedSize(300, 200)
        self.setWindowTitle("Configuration")

        layout = QVBoxLayout()

        #Dropdown
        layout_dropdown = QHBoxLayout()
        layout_dropdown.addWidget(QLabel("Choose Model:"))
        
        self.dir = os.path.dirname(os.path.abspath(__file__))
        self.dir = os.path.join(self.dir,"__models")
        self.models = [os.path.splitext(f)[0] for f in os.listdir(self.dir) if f.endswith(".keras") and os.path.isfile(os.path.join(self.dir,f))]

        self.dropdown = QComboBox()
        self.dropdown.addItem("None")
        self.dropdown.addItems(self.models)
        self.dropdown.addItem("Import...")
        selected_index =  self.dropdown.findText(self.model.name)
        if self.dropdown.findText(self.model.name) != -1:
            self.dropdown.setCurrentIndex(selected_index)

        self.dropdown.currentTextChanged.connect(self.drop_down_funct)

        layout_dropdown.addWidget(self.dropdown)

        #Description
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


        button_layout = QHBoxLayout()

        upload_button = QPushButton("Upload Config")
        # upload_button.clicked.connect(self.test)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)

        self.ok_button = QPushButton("Ok")
        self.ok_button.clicked.connect(self.Ok)  # closes the dialog
        self.ok_button.setDefault(True)
        
        button_layout.addWidget(upload_button)
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.ok_button)
        
        
        layout.addLayout(layout_dropdown)
        layout.addWidget(gb)
        layout.addLayout(button_layout)

        self.setLayout(layout)
    
    def drop_down_funct(self,text):
        
        if text == "Import...":
            file_path, _ = QFileDialog.getOpenFileName(self, "Import File", "", "Keras Model Files(*.keras)")
            if file_path:
                file_name = os.path.basename(file_path)
                dest_file_path = os.path.join(self.dir,file_name)

                if os.path.exists(dest_file_path):
                    reply = QMessageBox.question(
                        self,
                        "File Exists",
                        f"The file '{file_name}' already exists.\nDo you want to overwrite it?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        self.dropdown.setCurrentIndex(0)
                        return  

                try:
                    shutil.copy(file_path, dest_file_path)
                    print(f"Copied to: {dest_file_path}")
                    self.model = model(os.path.splitext(file_name)[0])
                    self.dropdown.insertItem(self.dropdown.count()-1, os.path.splitext(file_name)[0])
                    self.dropdown.setCurrentIndex(self.dropdown.count()-2)
                    #self.model = model(os.path.splitext(file_name)[0])

                except Exception as e:
                    print(f"Error: {e}")
                    os.remove(dest_file_path)
                    QMessageBox.warning(self,"Model not compatible", "Model Chosen is not compatible to run in this application. \nModel must be MFFSE or TCSSO", QMessageBox.Close, QMessageBox.Close)
                    if self.dropdown.findText(self.model.name) != -1:
                        self.dropdown.setCurrentIndex(self.dropdown.findText(self.model.name))
            else:
                self.dropdown.setCurrentIndex(0)
        else:
            if self.parent.model.name != text:
                self.ok_button.setText("Save and Apply")
                self.model = model(text)
            else:
                self.ok_button.setText("Ok")
                self.model = self.parent.model
            
        self.model_name_label.setText(self.model.name)
        self.model_input_label.setText(str(self.model.input_size))
        self.model_SM_size_label.setText(str(self.model.SM_size))
        self.model_SR_label.setText(str(self.model.SR))

    def Ok(self):
        if self.parent.model.name != self.model.name:
            if not UI_ONLY:
                if(self.parent.bt.send_config(self.model)==0):
                    QMessageBox.critical(self,"Error","Timeout while doing configuration")
                    return
            self.parent.model.setModel(self.model)    

        self.accept()