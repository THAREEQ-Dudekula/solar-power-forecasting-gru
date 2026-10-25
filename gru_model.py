"""
Solar Power Forecasting using Recurrent Neural Network (GRU)
GRU Model Architecture and Baseline Implementations

Student Name: DUDEKULA THAREEQ
Registration No: 2023008156
Domain: Renewable Energy
Assigned Architecture: GRU (Gated Recurrent Unit)
Assigned Optimization: Mini-Batch Gradient Descent
"""

import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import GRU, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam, SGD
from sklearn.linear_model import LinearRegression


def build_gru_model(seq_length, n_features, units_l1=64, units_l2=32, dropout_rate=0.20, learning_rate=0.001):
    """
    Constructs the assigned Gated Recurrent Unit (GRU) sequential neural network for time series regression.
    
    Architecture:
      1. Input Layer: (seq_length, n_features)
      2. GRU Layer 1: units_l1 recurrent memory units with reset/update gates (return_sequences=True)
      3. Dropout Layer: Regularization to prevent co-adaptation of weights
      4. GRU Layer 2: units_l2 recurrent units summarizing temporal dependencies (return_sequences=False)
      5. Dropout Layer: Regularization
      6. Dense Hidden Layer: 16 units with ReLU activation
      7. Dense Output Layer: 1 linear unit predicting solar PV power (MW)
      
    Optimization:
      Mini-Batch Gradient Descent (Adam/SGD with batch_size=32/64)
      Loss function: Mean Squared Error (MSE)
    """
    model = Sequential([
        Input(shape=(seq_length, n_features)),
        GRU(units_l1, return_sequences=True, activation='tanh', recurrent_activation='sigmoid'),
        Dropout(dropout_rate),
        GRU(units_l2, return_sequences=False, activation='tanh', recurrent_activation='sigmoid'),
        Dropout(dropout_rate),
        Dense(16, activation='relu'),
        Dense(1, activation='linear')
    ], name=f"GRU_SeqLen_{seq_length}")
    
    # Mini-Batch Optimizer: Adam with mini-batch updates
    optimizer = Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer, loss='mean_squared_error', metrics=['mae', 'root_mean_squared_error'])
    return model


class PersistenceBaseline:
    """
    Simple standard baseline for solar forecasting:
    Predicts the next hour's output based on the most recent observed hour:
      y_pred[t+1] = y[t]
    """
    def __init__(self):
        pass
    
    def predict(self, X_windows, last_observed_targets):
        """
        last_observed_targets is the last target value within each window.
        """
        return np.array(last_observed_targets).reshape(-1, 1)


class LinearRegressionBaseline:
    """
    Multivariate Linear Regression baseline:
    Flattens the historical sequence window (seq_length * n_features)
    and fits an ordinary least squares regression model.
    """
    def __init__(self):
        self.model = LinearRegression()
        
    def fit(self, X_train_windows, y_train_windows):
        n_samples = X_train_windows.shape[0]
        X_flat = X_train_windows.reshape(n_samples, -1)
        self.model.fit(X_flat, y_train_windows.ravel())
        return self
        
    def predict(self, X_windows):
        n_samples = X_windows.shape[0]
        X_flat = X_windows.reshape(n_samples, -1)
        preds = self.model.predict(X_flat)
        return preds.reshape(-1, 1)
