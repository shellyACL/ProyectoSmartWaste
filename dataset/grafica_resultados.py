# -*- coding: utf-8 -*-
"""
SmartWaste La Paz - Asignación de flota de camiones a zonas críticas
Basado en predicciones de la RNA 
"""

import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2
import folium
import matplotlib.pyplot as plt
# ============================================================
# 1. DATOS DE ENTRADA
# ============================================================

# Leer predicciones generadas por el Archivo 1
predicciones = pd.read_csv('predicciones.csv')
print("=== Predicciones cargadas ===")
print(predicciones.head())

# Cargar centroides de zonas 
centroides = pd.read_csv('centroides_zonas.csv')
centroides.rename(columns={'GDBSNOMB': 'nombre', 'centroide_lat': 'lat', 'centroide_lon': 'lon'}, inplace=True)

# Unir predicciones con coordenadas 
zonas_completas = predicciones.merge(centroides[['nombre', 'lat', 'lon']], on='nombre', how='left')

# Puntos fijos
GARAJE = {'nombre': 'Garaje Achumani', 'lat': -16.535331, 'lon': -68.074350}
RELLENO = {'nombre': 'Relleno Saka Churu', 'lat': -16.555393, 'lon': -68.131637}

# Capacidades
CAPACIDAD_CAMION_CONTENEDORES = 11  
CAMIONES_DISPONIBLES = 44  

# Parámetros operativos
TIEMPO_VACIADO_POR_CONTENEDOR_MIN = 7  
VELOCIDAD_PROMEDIO_KPH = 30
HORAS_TURNO = 6.5  

# ============================================================
# 2. FUNCIÓN DE DISTANCIA
# ============================================================

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# ============================================================
# 3. FILTRAR ZONAS CRÍTICAS 
# ============================================================
umbral = 70
zonas_criticas = zonas_completas[zonas_completas['prediccion'] >= umbral].copy()
zonas_criticas = zonas_criticas.sort_values('prediccion', ascending=False)

print(f"\n=== ZONAS CRÍTICAS (predicción >= {umbral}%) ===")
if zonas_criticas.empty:
    print("No hay zonas críticas. No se requiere recolección especial.")
    exit()

print(zonas_criticas[['nombre', 'prediccion', 'num_contenedores']])
print(f"\nTotal contenedores críticos: {zonas_criticas['num_contenedores'].sum()}")

# ============================================================
# 4. ASIGNACIÓN DE CAMIONES POR ZONA
# ============================================================

def asignar_camiones(zonas, capacidad_camion, camiones_disponibles):
    """Asigna camiones a cada zona según número de contenedores"""
    asignacion = []
    camiones_usados = 0
    
    for _, zona in zonas.iterrows():
        contenedores = zona['num_contenedores']
        nombre = zona['nombre']
        prediccion = zona['prediccion']
        
        # Calcular cuántos camiones necesita esta zona
        camiones_necesarios = (contenedores + capacidad_camion - 1) // capacidad_camion
        
        # Asignar
        asignacion.append({
            'zona': nombre,
            'prediccion': prediccion,
            'contenedores': contenedores,
            'camiones_asignados': camiones_necesarios,
            'contenedores_por_camion': contenedores / camiones_necesarios,
            'lat': zona['lat'],
            'lon': zona['lon']
        })
        camiones_usados += camiones_necesarios
    
    return asignacion, camiones_usados

asignacion, camiones_usados = asignar_camiones(
    zonas_criticas, CAPACIDAD_CAMION_CONTENEDORES, CAMIONES_DISPONIBLES
)

print("\n=== ASIGNACIÓN DE CAMIONES ===")
for a in asignacion:
    print(f"{a['zona']}: {a['contenedores']} contenedores → {a['camiones_asignados']} camiones")
print(f"\nTotal camiones necesarios: {camiones_usados}")
print(f"Camiones disponibles: {CAMIONES_DISPONIBLES}")
print(f"Camiones sobrantes: {CAMIONES_DISPONIBLES - camiones_usados}")

# ============================================================
# 5. CALCULAR MÉTRICAS POR CAMIÓN
# ============================================================

print("\n=== MÉTRICAS OPERATIVAS (por camión) ===")
for a in asignacion:
    # Distancias
    dist_garaje_zona = haversine(GARAJE['lat'], GARAJE['lon'], a['lat'], a['lon'])
    dist_zona_relleno = haversine(a['lat'], a['lon'], RELLENO['lat'], RELLENO['lon'])
    dist_relleno_garaje = haversine(RELLENO['lat'], RELLENO['lon'], GARAJE['lat'], GARAJE['lon'])
    
    distancia_total = dist_garaje_zona + dist_zona_relleno + dist_relleno_garaje
    
    # Tiempos
    tiempo_viaje_h = distancia_total / VELOCIDAD_PROMEDIO_KPH
    contenedores_por_camion = a['contenedores_por_camion']
    tiempo_vaciado_h = contenedores_por_camion * TIEMPO_VACIADO_POR_CONTENEDOR_MIN / 60
    tiempo_total_h = tiempo_viaje_h + tiempo_vaciado_h
    
    print(f"\n{a['zona']} (por camión):")
    print(f"  ├─ Distancias: garaje→zona={dist_garaje_zona:.2f} km, zona→relleno={dist_zona_relleno:.2f} km, relleno→garaje={dist_relleno_garaje:.2f} km")
    print(f"  ├─ Total recorrido: {distancia_total:.2f} km")
    print(f"  ├─ Tiempo viaje: {tiempo_viaje_h*60:.0f} min ({tiempo_viaje_h:.2f} h)")
    print(f"  ├─ Tiempo vaciado ({contenedores_por_camion:.1f} cont.): {tiempo_vaciado_h*60:.0f} min ({tiempo_vaciado_h:.2f} h)")
    print(f"  └─ Tiempo total: {tiempo_total_h*60:.0f} min ({tiempo_total_h:.2f} h)")

# ============================================================
# 6. VERIFICAR FACTIBILIDAD DEL TURNO
# ============================================================

tiempos_totales = []
for a in asignacion:
    dist_garaje_zona = haversine(GARAJE['lat'], GARAJE['lon'], a['lat'], a['lon'])
    dist_zona_relleno = haversine(a['lat'], a['lon'], RELLENO['lat'], RELLENO['lon'])
    dist_relleno_garaje = haversine(RELLENO['lat'], RELLENO['lon'], GARAJE['lat'], GARAJE['lon'])
    distancia_total = dist_garaje_zona + dist_zona_relleno + dist_relleno_garaje
    tiempo_viaje_h = distancia_total / VELOCIDAD_PROMEDIO_KPH
    tiempo_vaciado_h = a['contenedores_por_camion'] * TIEMPO_VACIADO_POR_CONTENEDOR_MIN / 60
    tiempos_totales.append(tiempo_viaje_h + tiempo_vaciado_h)

if max(tiempos_totales) <= HORAS_TURNO:
    print(f"\nTodos los camiones completan su ruta dentro del turno ({HORAS_TURNO} horas)")
else:
    print(f"\n Algunos camiones exceden el turno de {HORAS_TURNO} horas (máx {max(tiempos_totales):.2f} h)")
    print("   Se requiere turno vespertino o reasignación")

# Guarda plan de rutas
plan = pd.DataFrame(asignacion)
plan.to_csv('plan_rutas.csv', index=False)
print("\nPlan de rutas guardado en 'plan_rutas.csv'")

# ============================================================
# 7.1 FILTRAR ZONAS SIN COORDENADAS VÁLIDAS (Opción 1)
# ============================================================
print("\n=== Verificando coordenadas de las zonas críticas ===")
asignacion_validas = []
for a in asignacion:
    if pd.isna(a['lat']) or pd.isna(a['lon']):
        print(f"⚠️ Zona omitida por falta de coordenadas: {a['zona']}")
    else:
        asignacion_validas.append(a)

if len(asignacion_validas) == 0:
    print("❌ No hay zonas con coordenadas válidas. No se puede generar mapa.")
    exit()

print(f"✅ Zonas con coordenadas válidas: {len(asignacion_validas)} de {len(asignacion)}")

# Reemplazar la lista original por la filtrada
asignacion = asignacion_validas
# ============================================================
# 7. VISUALIZACIÓN: MAPA DE RUTAS Y GRÁFICO DE TIEMPOS
# ============================================================

mapa = folium.Map(location=[GARAJE['lat'], GARAJE['lon']], zoom_start=13)

# Marcadores
folium.Marker(
    location=[GARAJE['lat'], GARAJE['lon']],
    popup='Garaje Achumani',
    icon=folium.Icon(color='green', icon='home', prefix='fa')
).add_to(mapa)

folium.Marker(
    location=[RELLENO['lat'], RELLENO['lon']],
    popup='Relleno Saka Churu',
    icon=folium.Icon(color='red', icon='trash', prefix='fa')
).add_to(mapa)

# Colores para cada zona crítica
colores = ['blue', 'darkblue', 'purple', 'cadetblue', 'orange', 'darkred', 'lightred', 'beige', 'darkgreen', 'lightgreen']
for i, a in enumerate(asignacion):
    color = colores[i % len(colores)]
    # Marcar zona
    folium.Marker(
        location=[a['lat'], a['lon']],
        popup=f"{a['zona']}<br>Predicción: {a['prediccion']}<br>Contenedores: {a['contenedores']}<br>Camiones: {a['camiones_asignados']}",
        icon=folium.Icon(color=color, icon='info-sign')
    ).add_to(mapa)
    
    # Dibujar 
    puntos = [
        (GARAJE['lat'], GARAJE['lon']),
        (a['lat'], a['lon']),
        (RELLENO['lat'], RELLENO['lon']),
        (GARAJE['lat'], GARAJE['lon'])
    ]
    folium.PolyLine(puntos, color=color, weight=3, opacity=0.7, popup=f"Ruta {a['zona']}").add_to(mapa)

# Guarda mapa HTML
mapa.save('mapa_rutas.html')
print("Mapa interactivo guardado como 'mapa_rutas.html'")

# --- Gráfico de tiempos totales por camión (por zona) ---
nombres = [a['zona'] for a in asignacion]
tiempos_min = [a['contenedores_por_camion'] * TIEMPO_VACIADO_POR_CONTENEDOR_MIN + 
                (haversine(GARAJE['lat'], GARAJE['lon'], a['lat'], a['lon']) +
                 haversine(a['lat'], a['lon'], RELLENO['lat'], RELLENO['lon']) +
                 haversine(RELLENO['lat'], RELLENO['lon'], GARAJE['lat'], GARAJE['lon'])) / VELOCIDAD_PROMEDIO_KPH * 60
               for a in asignacion]

plt.figure(figsize=(10, 6))
bars = plt.bar(nombres, tiempos_min, color='skyblue')
plt.ylabel('Tiempo total por camión (minutos)')
plt.title('Tiempos estimados de recolección por zona crítica')
plt.xticks(rotation=45, ha='right')
for bar, t in zip(bars, tiempos_min):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{t:.0f} min', ha='center', va='bottom')
plt.tight_layout()
plt.savefig('tiempos_recoleccion.png')
plt.show()
print("Gráfico de tiempos guardado como 'tiempos_recoleccion.png'")