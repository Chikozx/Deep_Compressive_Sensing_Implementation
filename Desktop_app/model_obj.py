from PySide6.QtCore import QObject, Signal
import pywt
import numpy as np
import os
from config import UI_ONLY
if not UI_ONLY:
    import tensorflow as tf
    from keras.saving import register_keras_serializable

if not UI_ONLY:
    @register_keras_serializable()
    class AntipodalConstraint(tf.keras.constraints.Constraint):
        def __call__(self, w):
            return tf.sign(w)  # Forces weights to -1 or 1
    
    @register_keras_serializable()
    class ClippedCrossEntropyLoss(tf.keras.losses.Loss):
        def __init__(self, epsilon=1e-3,name='clipped_cross_entropy',reduction='sum_over_batch_size'):
            super().__init__(name,reduction)
            self.epsilon = epsilon

        def call(self, s, o):
            o = tf.clip_by_value(o, self.epsilon, 1 - self.epsilon)
            log_o = tf.clip_by_value(tf.math.log(o), tf.math.log(self.epsilon), tf.math.log(1-self.epsilon))
            log_1_o = tf.clip_by_value(tf.math.log(1.0-o), tf.math.log(self.epsilon), tf.math.log(1-self.epsilon))
            total_loss = -tf.reduce_sum(s*log_o) - tf.reduce_sum((1-s)*log_1_o)
            return total_loss  # Final loss value


class model(QObject):
    modelChanged = Signal()
    def __init__(self,name):
        super().__init__()
        if name == "None":
            self.name = name
            self.input_size = 256
            self.SM_size = None
            self.SR = None
            self.SM = None
            self.decoder = None
        else:
            if UI_ONLY:
                self.name = name
                self.input_size = 256
                self.SM_size = None
                self.SR = None
                self.SM = None
            else:
                self.name = name
                formatted = self.name +".keras"
                path  = os.path.join(os.path.dirname(os.path.abspath(__file__)),"__models",formatted)
                self.keras_model = tf.keras.models.load_model(path, custom_objects={"AntipodalConstraint": AntipodalConstraint, "ClippedCrossEntropyLoss": ClippedCrossEntropyLoss})
                
                if self.keras_model.name == "MFFSE":
                    self.input_size = self.keras_model.input_shape[1]
                    self.SM = self.keras_model.layers[2].weights[0].numpy().T
                    self.SM_size = self.SM.shape
                    self.SR = float(self.SM_size[0]/self.SM_size[1])
                    self.decoder = tf.keras.Model(inputs = self.keras_model.layers[2].output , outputs = self.keras_model.layers[-1].output)
                
                elif self.keras_model.name == "TCSSO":
                    self.input_size = self.keras_model.input_shape[1]
                    self.SM =  self.keras_model.layers[0].weights[0].numpy().T
                    self.SM_size = self.SM.shape
                    self.SR = float(self.SM_size[0]/self.SM_size[1])
                    
                    x = self.keras_model.layers[0].output
                    for layer in self.keras_model.layers[1:]:
                        x = layer(x)
                    self.decoder = tf.keras.Model(inputs=self.keras_model.layers[0].output, outputs=x) 

                else:
                    raise ValueError("Model is not MFFSE model type")
                
    #Uji coba untuk TCSSO
    def reconstruct_signal(self, y, o_min=(80/100)):
        #Prediksi support
        o_pred = self.decoder.predict(y.reshape(1,y.shape[0]))
        supp_hat = (o_pred >= o_min).astype(int)

        S_ = pywt.wavedec(np.eye(256), 'rbio3.9', level=4, mode='per')
        S = np.concatenate(S_,axis=1)
        A_S = self.SM@S

        A_S_sub = A_S[:,supp_hat[0]==1]  # Select columns corresponding to the support
        A_S_sub_pinv = np.linalg.pinv(A_S_sub)  # Calculate pseudo-inverse
        s_hat_sub = A_S_sub_pinv @ y  # Get coefficients

        s_hat = np.zeros(256)
        s_hat[supp_hat[0]==1] = s_hat_sub
        
        return S@s_hat

    def reconstruct_signal_autoencoder(self, x, o_min=(80/100)):
        y = self.SM@x
        #Prediksi support
        o_pred = self.decoder.predict(y.reshape(1,y.shape[0]))
        supp_hat = (o_pred >= o_min).astype(int)

        S_ = pywt.wavedec(np.eye(256), 'rbio3.9', level=4, mode='per')
        S = np.concatenate(S_,axis=1)
        A_S = self.SM@S

        A_S_sub = A_S[:,supp_hat[0]==1]  # Select columns corresponding to the support
        A_S_sub_pinv = np.linalg.pinv(A_S_sub)  # Calculate pseudo-inverse
        s_hat_sub = A_S_sub_pinv @ y  # Get coefficients

        s_hat = np.zeros(256)
        s_hat[supp_hat[0]==1] = s_hat_sub
        
        return S@s_hat

    def setModel(self, other_model):
        self.name = other_model.name
        self.input_size = other_model.input_size
        self.SM_size = other_model.SM_size
        self.SR = other_model.SR
        self.SM = other_model.SM
        self.decoder = other_model.decoder
        self.keras_model = other_model.keras_model
        self.modelChanged.emit()