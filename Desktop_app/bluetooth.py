# Copyright 2026 Joseph Maximillian Bonaventura Chico Reginald Jansen
# Licensed under the Apache License, Version 2.0 (the "License");

import numpy as np
from PySide6.QtSerialPort import QSerialPort
from PySide6.QtCore import QIODevice, Signal, QObject, Slot, QMetaMethod
from PySide6.QtWidgets import QMessageBox
from config import UI_ONLY
if not UI_ONLY:
    import tensorflow as tf
    #For Sanity Check
    from keras.saving import register_keras_serializable

import time

class bluetooth(QObject):
    Data_ready = Signal(object)
    Data_ready_no_work = Signal(object)

    #For Sanity Check
    Data_Ready_all_Encoder =  Signal(object)

    def __init__(self, tab = None):
        super().__init__()
        self.serial = QSerialPort()
        self.serial.setBaudRate(QSerialPort.Baud9600)
        
        self.tab = tab
        self.is_connected = False
        self.ser = None
        self.mode = 0

        #For Sanity Check
        self.step_len = 0
        self.buffer = []

        # self.bl_x = []
        # self.bl_y = []
        # self.data_state = 0
        self.is_transmit = False
        self.port_name = None


    def set_port(self,port_name):
        self.port_name = port_name
        self.serial.setPortName(port_name)

    def bt_connect(self):
        if self.port_name is None or self.port_name=="Select Port":
            QMessageBox.critical(self.tab, "Error", "Please Select a valid port")
        else:
            if self.serial.open(QIODevice.ReadWrite):
                QMessageBox.information(self.tab,"Success", "Connected to serial port!")
                self.is_connected = True
                self.serial.readyRead.connect(self.handle_data_received)
            else:
                QMessageBox.critical(self.tab, "Error", f"Failed to open port:\n{self.serial.errorString()}")
    
            
    def bt_dissconnect(self):
        self.serial.close()
        self.is_connected = False

    def bt_start(self):
        if self.is_connected:
            msg = "start\n"
            self.serial.write(msg.encode('utf-8'))
            self.mode=2
        else:
            print("serial not connected")

    def bt_stop(self):
        if self.is_connected:
            msg = "stop\n"
            self.serial.write(msg.encode('utf-8'))
        else:
            print("serial not connected")
    
    def bt_step(self, len, mode):
        if mode == "MO0":
            print("mode no compress")
            self.mode=0
        elif mode == "MODD":
            print("Mode all compress")
            self.mode=4
        else:
            print("Compression Mode")
            self.mode=1

        if self.is_connected:
            frame_size =  int(len)
            
            # For Sanity Check
            self.step_len = frame_size
            step_cmd = "step0" if mode == "MO0" or mode == "MODD" else "step1"
            step_cmd = step_cmd.encode()
            buf = bytearray()
            buf.extend(step_cmd)
            buf.extend(frame_size.to_bytes())
            self.serial.write(buf)
            
        else:
            print("serial not connected")
	
    def handle_data_received(self):
        if self.mode == 0:
            data = self.serial.read(256).data()
            if(data):
                arr = np.frombuffer(data,dtype='<i4')
                self.Data_ready_no_work.emit(arr)
         
        elif self.mode == 1:
            data = self.serial.readAll().data()
            if(data):
                m = self.tab.model.SM_size[0]
                print(f"Data Received size: {len(data)}")
                arr = np.frombuffer(data[0:m*4],dtype='<f4')
                mm = np.frombuffer(data[m*4:],dtype='<i4')
                df = data_frame(arr,mm[0],mm[1])
                
                print(f"MODE 1 Data length: {len(arr)}, Max: {mm[0]}, Min: {mm[1]}")
                self.buffer.append(df)

                if(len(self.buffer)==self.step_len):
                    self.Data_ready.emit(self.buffer)
                    self.buffer=[]
                
        elif self.mode == 2:
            data = self.serial.readAll().data()
            if(data):
                arr = np.frombuffer(data,dtype='<i4')
                self.Data_ready_no_work.emit(arr)

        #For Sanity Check
        elif self.mode == 4:
            data = self.serial.read(512).data()
            if(data):
                arr = np.frombuffer(data,dtype='<i4')
                self.buffer.extend(arr)
                if(len(self.buffer) == 256 * self.step_len):
                    self.Data_Ready_all_Encoder.emit(self.buffer)
                    self.buffer=[]        
        

    def config_ack(self):
        if self.serial.waitForReadyRead(1000):
            data = self.serial.readAll().data()
            if(data == b'ACK'):
                return 1
            else:
                return 0
        else:
            print("timeout")
            return 0 
        
    def send_config(self, model):
        rr_sig = QMetaMethod.fromSignal(self.serial.readyRead)
        while self.serial.isSignalConnected(rr_sig):
            self.serial.readyRead.disconnect(self.handle_data_received)

        if self.serial.isSignalConnected(rr_sig)==1:
            print("masih ada")

        #Send config command
        msg = "config"
        self.serial.write(msg.encode("utf-8"))
        if self.config_ack() !=1: return 0

        #Send Model Name
        msg = f"M:{model.name}"
        self.serial.write(msg.encode("utf-8"))
        if self.config_ack() !=1: return 0
        
        #Send SM Size
        msg = f"S:".encode("utf-8")
        msg = bytearray(msg)
        msg.extend(model.SM_size[0].to_bytes(2,"little"))
        msg.extend(model.SM_size[1].to_bytes(2,"little")) 
        self.serial.write(msg)
        if self.config_ack() !=1: return 0

        if model.SM is not None and model.SM.size>0 :
            bits = (model.SM == 1).astype(np.uint8)
            n, m = bits.shape
            pad_len = (-m) % 8
            if pad_len > 0:
                bits = np.pad(bits, ((0,0), (0,pad_len)), constant_values=0)
            print(bits[0])
            bytes_array = np.packbits(bits, axis=1)
            print(bytes_array[0])
            
            for i in range (len(bytes_array)):
                #Send SM Size
                msg = f"D:".encode("utf-8")
                msg = bytearray(msg)
                msg.extend(bytes_array[i].tobytes())
                self.serial.write(msg)
                if self.config_ack() !=1: return 0
        else:
            msg = f"D:".encode("utf-8")
            msg = bytearray(msg)
            msg.extend(0x00)
            self.serial.write(msg)
            if self.config_ack() !=1: return 0
        
        msg = "config_done".encode("utf-8")
        msg = bytearray(msg)
        self.serial.write(msg)
        if self.config_ack() !=1: return 0
        
        self.serial.readyRead.connect(self.handle_data_received)
        return 1


if not UI_ONLY:
    @register_keras_serializable()
    class AntipodalConstraint(tf.keras.constraints.Constraint):
        def __call__(self, w):
            return tf.sign(w)  # Forces weights to -1 or 1


class Data_Prediction_Sanity(QObject):
    Prediction_done = Signal(object)
    model = tf.keras.models.load_model("__models/MFFSE_SR_0_41_fix.keras",custom_objects={"AntipodalConstraint": AntipodalConstraint})
    norm_data=[]

    @Slot(object)
    def pred(self,data):
        l = int(len(data)/256)
        split_data = np.zeros((l,256))
        for i in range(l):
            split_data[i] = data[i*256:(i*256)+256]
        
        split_data_norm = np.zeros((l,256))
        for i in range(l):
            split_data_norm[i] = (split_data[i] - np.min(split_data[i]))/(np.max(split_data[i])-np.min(split_data[i]))
        
        output = self.model(split_data_norm)
        print(f"Data len san worker {split_data_norm.shape}")
        print(f"Output shape {output.shape}")
        self.Prediction_done.emit(output)



class Data_Prediction_Worker(QObject):
    Prediction_done = Signal(object)

    if not UI_ONLY:    
        def __init__(self, tab=None):
            super().__init__(tab)
            self.tab = tab
            
        @Slot(object)
        def start_prediction(self, data):
            prediction_buffer = np.zeros((len(data),data[0].data.shape[0]))
            
            for i in range (len(data)):
                prediction_buffer[i] = data[i].data

            if self.tab.model.keras_model.name == "MFFSE":
                y = self.tab.model.decoder(prediction_buffer)
                y = np.array(y)
                for i in range(len(data)):
                    y[i,:,0] = (y[i,:,0] * (data[i].max - data[i].min)) + data[i].min
                
                y = np.squeeze(y)
                self.Prediction_done.emit(y)

            elif self.tab.model.keras_model.name == "TCSSO":
                y = np.empty((len(data),256))
                for i in range(len(prediction_buffer)):
                    y[i] = self.tab.model.reconstruct_signal(prediction_buffer[i])
                
                for i in range(len(data)):
                    y[i] = (y[i] * (data[i].max - data[i].min)) + data[i].min
                
                self.Prediction_done.emit(y)


            # To Check For Time
            # start = time.perf_counter()
            # y = self.Model(data.reshape(1,data.shape[0]))
            # print(data)
            # end = time.perf_counter()
            # print(f"Time spent calculating : {end-start:.5f} Seconds")
            # self.Prediction_done.emit(y)

class data_frame():
    def __init__(self,data,max,min):
        self.data = data
        self.min = min
        self.max = max