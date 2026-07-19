# backend/train_pipeline.py
import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from sqlalchemy import create_engine
import os

DATABASE_URL = "postgresql://admin:admin@localhost:5433/smartwaste_db"

def extraer_datos_entrenamiento():
    """
    Simula la extracción del histórico de llenado acumulado en la base de datos.
    En producción'.
    """
    print("Extrayendo datos históricos desde PostgreSQL...")
    
    # generamos un DataFrame si que no hay reeigistro suficientes 
    np.random.seed(42)
    n_muestras = 1000
    
    datos = {
        'zona_id': np.random.randint(1, 10, n_muestras),          
        'llenado_ayer': np.random.uniform(0, 100, n_muestras),    # Porcentaje 0-100
        'dia_semana': np.random.randint(1, 8, n_muestras),        # 1 a 7
        'feria_ayer': np.random.randint(0, 2, n_muestras),        # 0 o 1
        'num_contenedores': np.random.randint(1, 15, n_muestras), # Cantidad en la zona
        'topografia': np.random.randint(0, 3, n_muestras),        # 0: Plano, 1: Pendiente, 2: Alta pendiente
        'clima_mañana': np.random.randint(0, 2, n_muestras),      # 0: Despejado, 1: Lluvia/Frente Frío
        'bloqueo_ayer': np.random.randint(0, 2, n_muestras),      # 0 o 1 (Clásico de La Paz)
        'porcentaje_llenado_real': np.random.uniform(10, 100, n_muestras) # Target (Lo que queremos predecir)
    }
    
    return pd.DataFrame(datos)

def entrenar_cerebro_predictivo():
    df = extraer_datos_entrenamiento()
    X = pd.DataFrame()
    X['zona'] = df['zona_id'] / 10.0                          
    X['llenado_ayer'] = df['llenado_ayer'] / 100.0            # Escala 0 a 1
    X['dia'] = (df['dia_semana'] - 1) / 6.0                   # Escala 0 a 1
    X['feria'] = df['feria_ayer'].astype(float)
    X['num_cont'] = df['num_contenedores'] / 50.0             # Escalado a un tope de 50 contenedores
    X['topografia'] = df['topografia'] / 2.0                  # 3 niveles (0, 0.5, 1.0)
    X['clima'] = df['clima_mañana'].astype(float)
    X['bloqueo'] = df['bloqueo_ayer'].astype(float)
    
    y = df['porcentaje_llenado_real'] / 100.0                 # Target normalizado 0 a 1
    
    print("[TensorFlow] Diseñando la arquitectura de la Red Neuronal...")
    model = Sequential([
        Dense(64, activation='relu', input_shape=(8,)),
        Dropout(0.1),
        Dense(32, activation='relu'),
        Dense(16, activation='relu'),
        Dense(1, activation='sigmoid') 
    ])
    
    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])
    
    print("[TensorFlow] Entrenando el modelo...")
    model.fit(X, y, epochs=15, batch_size=32, validation_split=0.2, verbose=1)
    model_name = "smartwaste_modelo.keras"
    model.save(model_name)
    print(f"¡Modelo guardado con éxito como '{model_name}'!.")

if __name__ == "__main__":
    entrenar_cerebro_predictivo()