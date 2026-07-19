# -*- coding: utf-8 -*-
"""
Script para asignar contenedores (KML) a zonas (shapefile) y contar por zona.
Autor: Asistente IA
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# ------------------------------------------------------------
# CONFIGURACIÓN: cambia estos nombres según tus archivos
# ------------------------------------------------------------
ARCHIVO_ZONAS_SHP = "zonas/zonas.shp"          # nombre del shapefile de zonas
ARCHIVO_CONTENEDORES_KML = "contenedores.kml"   # tu archivo KML
ARCHIVO_SALIDA_CSV = "num_contenedores_por_zona.csv"
ARCHIVO_CENTROIDES_CSV = "centroides_zonas.csv"
# ------------------------------------------------------------
# 1. Cargar el shapefile de zonas
# ------------------------------------------------------------
print("Cargando shapefile de zonas...")
mapa_zonas = gpd.read_file(ARCHIVO_ZONAS_SHP)

# Ver las columnas disponibles para identificar la que contiene el nombre o código de zona
print("Columnas disponibles en el shapefile:")
print(mapa_zonas.columns.tolist())
print("\nPrimeras filas del shapefile:")
print(mapa_zonas.head())

# ------------------------------------------------------------
# 2. Preguntar al usuario cuál columna usar para identificar zonas
# ------------------------------------------------------------
columna_zona = input("\n¿Cuál es el nombre de la columna que identifica la zona (ej. COD_ZONA, NOM_ZONA)?: ")

if columna_zona not in mapa_zonas.columns:
    print(f"Error: La columna '{columna_zona}' no existe. Usando la primera columna.")
    columna_zona = mapa_zonas.columns[0]

print(f"Usando columna: {columna_zona}")

# ------------------------------------------------------------
# 3. Cargar el KML de contenedores
# ------------------------------------------------------------
print("\nCargando archivo KML de contenedores...")
contenedores = gpd.read_file(ARCHIVO_CONTENEDORES_KML, driver='KML')

# Asegurar que ambos tengan el mismo sistema de coordenadas (CRS)
# El KML normalmente está en WGS84 (EPSG:4326). Forzamos el shapefile a ese CRS si es necesario.
if mapa_zonas.crs != contenedores.crs:
    print(f"Reproyectando zonas a CRS de contenedores: {contenedores.crs}")
    mapa_zonas = mapa_zonas.to_crs(contenedores.crs)

# ------------------------------------------------------------
# 4. Unión espacial: asignar a cada contenedor la zona donde está contenido
# ------------------------------------------------------------
print("Realizando unión espacial (point-in-polygon)...")
contenedores_con_zona = gpd.sjoin(contenedores, mapa_zonas, how="left", predicate="within")

# ------------------------------------------------------------
# 5. Contar contenedores por zona
# ------------------------------------------------------------
conteo = contenedores_con_zona.groupby(columna_zona).size().reset_index(name='num_contenedores')

# Ordenar de mayor a menor cantidad
conteo = conteo.sort_values('num_contenedores', ascending=False)

# ------------------------------------------------------------
# 6. Guardar resultado y mostrar resumen
# ------------------------------------------------------------
conteo.to_csv(ARCHIVO_SALIDA_CSV, index=False)
print(f"\n¡Proceso completado! Se generó '{ARCHIVO_SALIDA_CSV}'")
print("\nResumen de contenedores por zona (primeras 10):")
print(conteo.head(10))

print("\nCalculando centroides por zona...")

# Extraer coordenadas (longitud, latitud) de los contenedores
# Asumiendo que la geometría es Point
contenedores_con_zona['lon'] = contenedores_con_zona.geometry.x
contenedores_con_zona['lat'] = contenedores_con_zona.geometry.y

# Agrupar por zona y calcular el centroide (promedio de coordenadas)
centroides = contenedores_con_zona.groupby(columna_zona).agg(
    centroide_lon=('lon', 'mean'),
    centroide_lat=('lat', 'mean'),
    num_contenedores=('lon', 'count')
).reset_index()

# Guardar centroides
centroides.to_csv(ARCHIVO_CENTROIDES_CSV, index=False)
print(f"Centroides guardados en '{ARCHIVO_CENTROIDES_CSV}'")
print("\nPrimeros 5 centroides:")
print(centroides.head())
# Opcional: guardar también los contenedores con su zona asignada (para depuración)
contenedores_con_zona.to_file("contenedores_asignados.geojson", driver='GeoJSON')
print("Además se guardó 'contenedores_asignados.geojson' para visualización en QGIS o Google Earth.")