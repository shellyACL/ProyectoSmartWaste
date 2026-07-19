
import requests
from typing import Dict, List, Tuple

class OSRMService:
    def __init__(self):
        self.base_url = "http://router.project-osrm.org/route/v1/driving"

    def calcular_ruta_real(self, puntos: List[Tuple[float, float]]) -> Dict:
        """
        Recibe una lista de tuplas (lat, lon) y calcula la ruta real por calles.
        Ejemplo de entrada: [(-16.5353, -68.0743), (-16.5553, -68.1316)]
        """
        coordenadas_formateadas = ";".join([f"{lon},{lat}" for lat, lon in puntos])
        
        url = f"{self.base_url}/{coordenadas_formateadas}?overview=false&steps=false"
        
        try:
            respuesta = requests.get(url, timeout=5)
            datos = respuesta.json()
            
            if datos.get("code") == "Ok":
                ruta_optima = datos["routes"][0]
                
                return {
                    "exito": True,
                    "distancia_metros": ruta_optima["distance"],
                    "tiempo_segundos": ruta_optima["duration"]
                }
            return {"exito": False, "error": f"OSRM Error: {datos.get('code')}"}
            
        except requests.exceptions.RequestException as e:
            return {"exito": False, "error": f"Fallo de conexión con OSRM: {str(e)}"}
        
    def optimizar_viaje_multiples_puntos(self, puntos: list[tuple[float, float]]) -> dict:
        """
        Recibe una lista de tuplas (lat, lon). El primer punto DEBE ser el Garaje.
        OSRM calculará el orden óptimo de visita calle por calle.
        """
        if len(puntos) < 2:
            return {"exito": False, "error": "Necesitas al menos 2 puntos para generar una ruta."}

        coordenadas_formateadas = ";".join([f"{lon},{lat}" for lat, lon in puntos])

        url = f"http://router.project-osrm.org/trip/v1/driving/{coordenadas_formateadas}?source=first&overview=false"
        
        try:
            respuesta = requests.get(url, timeout=10)
            datos = respuesta.json()
            
            if datos.get("code") == "Ok":
                viaje_optimizado = datos["trips"][0]
                orden_sugerido = [wp["waypoint_index"] for wp in datos["waypoints"]]
                
                return {
                    "exito": True,
                    "distancia_total_km": viaje_optimizado["distance"] / 1000,
                    "tiempo_total_minutos": viaje_optimizado["duration"] / 60,
                    "orden_visita_optimo": orden_sugerido # Ejemplo: [0, 3, 1, 2]
                }
            return {"exito": False, "error": f"OSRM Trip Error: {datos.get('code')}"}
        except Exception as e:
            return {"exito": False, "error": f"Error de conexión: {str(e)}"}