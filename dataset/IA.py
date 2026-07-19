"""
SmartWaste La Paz - Normalización de datos
Proyecto: RNA para predicción de llenado de contenedores
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.metrics import MeanAbsoluteError

# ============================================================
# PARTE 1: NORMALIZACIÓN DE DATOS
# ============================================================

# Archvivo donde la ia va a practicar

df = pd.read_csv('entrenamiento.txt')

# Definimos  max y min, que se obtiene de los datos raales o los dataset
min_max = {
    'zona': {'min': 1, 'max': 78},
    'llenado_ayer': {'min': 0, 'max': 100},
    'dia_semana_mañana': {'min': 1, 'max': 7},
    'feria_ayer': {'min': 0, 'max': 1},
    'num_contenedores': {'min': 1, 'max': 46},
    'topografia': {'min': 0, 'max': 2},
    'clima_mañana': {'min': 0, 'max': 1},
    'bloqueo_ayer': {'min': 0, 'max': 1},
    'llenado_mañana_real': {'min': 0, 'max': 100}
}

# Función para normalizar una columna al rango [0, 1]

def normalizar(columna, valores):
    """Normaliza una columna usando min y max definidos"""
    minimo = min_max[columna]['min']
    maximo = min_max[columna]['max']
    return (valores - minimo) / (maximo - minimo)

# Aplicar normalización a cada columna

X_columns = ['zona', 'llenado_ayer', 'dia_semana_mañana', 'feria_ayer',
             'num_contenedores', 'topografia', 'clima_mañana', 'bloqueo_ayer']

# Variable de salida (y)
y_column = 'llenado_mañana_real'

# Crear DataFrame normalizado
df_norm = pd.DataFrame()

for col in X_columns:
    df_norm[col] = normalizar(col, df[col])

# Normalizar la salida
df_norm[y_column] = normalizar(y_column, df[y_column])

# Mostrar resultados
print("=== Datos originales (primeras 5 filas) ===")
print(df.head())
print("\n=== Datos normalizados (primeras 5 filas) ===")
print(df_norm.head())

print("\n=== Rangos después de normalización ===")
for col in df_norm.columns:
    print(f"{col}: min={df_norm[col].min():.4f}, max={df_norm[col].max():.4f}")

# Guardar datos normalizados (por si acaso)
df_norm.to_csv('datos_residuos_normalizados.csv', index=False)
print("\nArchivo 'datos_residuos_normalizados.csv' guardado.")

# Separar X (entradas) y y (salida) para la red neuronal

X = df_norm[X_columns].values  # Matriz de 8 columnas
y = df_norm[y_column].values   # Vector de 1 columna

print(f"\nForma de X (entradas): {X.shape}")  # (n_filas, 8)
print(f"Forma de y (salida): {y.shape}")      # (n_filas,)

# ============================================================
# PARTE 2:  ENTRENAMIENTO Y PRUEBA
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"\nEntrenamiento: {X_train.shape[0]} muestras")
print(f"Prueba: {X_test.shape[0]} muestras")

# ============================================================
# PARTE 3: CONSTRUCCIÓN DE LA RED NEURONAL (Keras)
# ============================================================
# Se pasa la arquitectura y las Funciones de activación
model = Sequential([
    Dense(6, activation='relu', input_dim=8, name='capa_oculta_1'),
    Dense(3, activation='relu', name='capa_oculta_2'),
    Dense(1, activation='sigmoid', name='capa_salida')
])

# Compilar el modelo
model.compile(
    optimizer=Adam(learning_rate=0.01),
    loss='mean_squared_error',
    metrics=[MeanAbsoluteError(name='mae')]
)

# Resumen de la arquitectura
print("\n=== Arquitectura de la Red Neuronal ===")
model.summary()

# ============================================================
# PARTE 4: ENTRENAMIENTO
# ============================================================

print("\n=== Entrenando la red... ===")
history = model.fit(
    X_train, y_train,
    epochs=100,
    batch_size=4,
    validation_split=0.2,
    verbose=1
)

# ============================================================
# PARTE 5: EVALUACIÓN DEL MODELO
# ============================================================
print("\n=== Evaluación en datos de prueba ===")
loss, mae = model.evaluate(X_test, y_test, verbose=0)
print(f"Pérdida (MSE): {loss:.4f}")
print(f"Error absoluto medio (MAE) normalizado: {mae:.4f}")
print(f"Error absoluto medio en porcentaje: {mae * 100:.2f}%")

# ============================================================
# PARTE 6: PREDICCIÓN CON UN EJEMPLO NUEVO
# ============================================================
print("\n=== Predicción de ejemplo ===")

nueva_muestra_original = np.array([[3, 70, 5, 1, 37, 2, 0, 0]])
nueva_muestra_norm = np.array([[
    (3-1)/77,      # zona
    70/100,        # llenado_ayer
    (5-1)/6,       # dia_semana
    1.0,           # feria
    (37-1)/45,     # num_contenedores
    2/2,           # topografia
    0.0,           # clima
    0.0            # bloqueo
]])

prediccion_norm = model.predict(nueva_muestra_norm, verbose=0)
prediccion_porcentaje = prediccion_norm[0][0] * 100

print(f"Datos de entrada: zona=3 (COTA COTA), llenado_ayer=70%, día=5, feria=1, contenedores=37, topografía=2, clima=0, bloqueo=0")
print(f"Predicción de la red: {prediccion_porcentaje:.2f}%")
print(f"Valor real esperado: 88%")

# ============================================================
# PARTE 7: GUARDAR EL MODELO 
# ============================================================
model.save('smartwaste_modelo.keras')
print("\nModelo guardado como 'smartwaste_modelo.keras'")

# ============================================================
# PARTE 8: GENERAR PREDICCIONES 
# ============================================================
print("\n=== Generando predicciones (último registro por zona) ===")

mapeo_nombres = {
    1: "IRPAVI BAJO",
    2: "SAN MIGUEL",
    3: "COTA COTA",
    4: "MIRAFLORES",
    5: "VILLA COPACABANA",
    6: "ACHUMANI",
    7: "PAMPAHASI ALTO",
    8: "ALTO SOPOCACHI",
    9: "OBRAJES",
    10: "CHASQUIPAMPA",
    11: "PURA PURA",
    12: "SAN JORGE",
    13: "COSMOS",
    14: "SOPOCACHI",
    15: "ALTO OBRAJES",
    16: "LOS ANDES",
    17: "ALTO SAN PEDRO",
    18: "LA BARQUETA JARDIN",
    19: "MESETA DE ACHUMANI",
    20: "EL TEJAR",
    21: "KOANI ALTO IRPAVI",
    22: "PAMPAHASI BAJO",
    23: "VILLA SAN ANTONIO",
    24: "VILLA SALOME",
    25: "BARRIO PETROLERO",
    26: "MIRAFLORES CENTRO",
    27: "MUNAYPATA",
    28: "CALACOTO",
    29: "MALLASILLA",
    30: "MIRAFLORES BAJO",
    31: "IRPAVI II",
    32: "BAJO SEGUENCOMA",
    33: "TEMBLADERANI",
    34: "ACHACHICALA",
    35: "VILLA VICTORIA",
    36: "ALTO SEGUENCOMA",
    37: "VILLA EL CARMEN",
    38: "ALTO TEJAR",
    39: "8 DE DICIEMBRE",
    40: "MALLASA",
    41: "PARQUE URBANO CENTRA",
    42: "VILLA FATIMA",
    43: "ALTO MIRAFLORES",
    44: "BELEN",
    45: "OBISPO INDABURU",
    46: "AUQUISAMAÑA",
    47: "BELLA VISTA",
    48: "GRAN PODER",
    49: "CIUDADELA FERROVIARIA",
    50: "ROSARIO",
    51: "BAJO SAN ANTONIO",
    52: "SAN PEDRO",
    53: "CHALLAPAMPA",
    54: "VILLA NUEVO POTOSI",
    55: "SANTA BARBARA",
    56: "ARANJUEZ",
    57: "LOS ROSALES",
    58: "LA MERCED",
    59: "VILLA PABON",
    60: "LA FLORIDA",
    61: "ALTO PURA PURA",
    62: "IRPAVI I",
    63: "TACAGUA",
    64: "JUPAPINA",
    65: "JARDIN DE LA REVOLUCION",
    66: "AMOR DE DIOS",
    67: "EL PRADO JARDIN",
    68: "MARISCAL SANTA CRUZ",
    69: "PARQUE ZOOLOGICO",
    70: "COLMIL",
    71: "PLAN AUTOPISTA",
    72: "AGUA DE LA VIDA",
    73: "23 DE MARZO",
    74: "CASCO URBANO CENTRAL",
    75: "18 DE MAYO",
    76: "KOKENI LAS ROSAS",
    77: "CHICANI",
    78: "ESCOBAR URIA"
}

ultimos_registros = df.groupby('zona').last().reset_index()

# Normalizar los últimos registros 
ultimos_norm = pd.DataFrame()
for col in X_columns:
    ultimos_norm[col] = normalizar(col, ultimos_registros[col])

# Predecir
X_ultimos = ultimos_norm[X_columns].values
predicciones_ultimos = model.predict(X_ultimos, verbose=0).flatten() * 100

# Crear DataFrame de resultados 
resultados = ultimos_registros[['zona', 'num_contenedores']].copy()
resultados['prediccion'] = predicciones_ultimos
resultados['nombre'] = resultados['zona'].map(mapeo_nombres)

# Guardar CSV
resultados.to_csv('predicciones.csv', index=False)
print("Archivo 'predicciones.csv' guardado con una predicción por zona (último registro histórico).")
print("\nMuestra de las primeras 10 filas:")
print(resultados.head(10))