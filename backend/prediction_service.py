
import numpy as np
from tensorflow.keras.models import load_model
import os

class PredictionService:
    def __init__(self):
        self.model_path = 'smartwaste_modelo.keras'
        self.model = None
        
        if os.path.exists(self.model_path):
            self.model = load_model(self.model_path)
            print("[IA] Modelo de TensorFlow cargado exitosamente.")
        else:
            print("[IA] Archivo 'smartwaste_modelo.keras' no encontrado. La predicción usará valores base hasta el reentrenamiento.")

    def predecir_llenado(self, datos_contenedor: dict) -> float:
        """
        Recibe los datos actuales de un contenedor y usa la red neuronal 
        para predecir el porcentaje de llenado de mañana.
        """
        if not self.model:
            return 50.0

        try:
            zona_norm = (datos_contenedor['zona'] - 1) / 77
            llenado_ayer_norm = datos_contenedor['llenado_ayer'] / 100
            dia_norm = (datos_contenedor['dia_semana_mañana'] - 1) / 6
            feria_norm = float(datos_contenedor['feria_ayer'])
            num_cont_norm = (datos_contenedor['num_contenedores'] - 1) / 45
            topografia_norm = datos_contenedor['topografia'] / 2
            clima_norm = float(datos_contenedor['clima_mañana'])
            bloqueo_norm = float(datos_contenedor['bloqueo_ayer'])

            entrada_norm = np.array([[
                zona_norm, llenado_ayer_norm, dia_norm, feria_norm,
                num_cont_norm, topografia_norm, clima_norm, bloqueo_norm
            ]])

            prediccion_norm = self.model.predict(entrada_norm, verbose=0)
            
            return float(prediccion_norm[0][0] * 100)
            
        except Exception as e:
            print(f"Error al procesar predicción: {str(e)}")
            return 50.0