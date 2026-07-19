# -*- coding: utf-8 -*-
"""
Script para procesar archivo KML de contenedores y asignar número de contenedores por zona.
Autor: Asistente IA
Uso: python procesar_kml_contenedores.py
"""

import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

# ------------------------------
# 1. Cargar el archivo KML
# ------------------------------
kml_file = "contenedores.kml"   # Cambia por la ruta de tu archivo
tree = ET.parse(kml_file)
root = tree.getroot()

# Namespace típico de KML
ns = {'kml': 'http://www.opengis.net/kml/2.2'}

# ------------------------------
# 2. Extraer todas las coordenadas
# ------------------------------
coordenadas = []
for placemark in root.findall('.//kml:Placemark', ns):
    point = placemark.find('.//kml:Point', ns)
    if point is not None:
        coords_str = point.find('.//kml:coordinates', ns).text.strip()
        # Las coordenadas vienen como "lon,lat,alt" (altitud opcional)
        lon, lat = coords_str.split(',')[0:2]
        coordenadas.append([float(lon), float(lat)])

print(f"Total de contenedores encontrados: {len(coordenadas)}")

# Convertir a numpy array
X = np.array(coordenadas)

# ------------------------------
# 3. Clustering (K-means) en 5 zonas
# ------------------------------
num_zonas = 5   # Puedes cambiar según tus zonas reales
kmeans = KMeans(n_clusters=num_zonas, random_state=42, n_init=10)
kmeans.fit(X)
labels = kmeans.labels_

# Añadir etiquetas a un DataFrame
df = pd.DataFrame(X, columns=['longitud', 'latitud'])
df['cluster'] = labels

# ------------------------------
# 4. Contar contenedores por cluster
# ------------------------------
conteo = df['cluster'].value_counts().sort_index()
print("\nNúmero de contenedores por cluster:")
for c in range(num_zonas):
    print(f"  Zona {c+1} (cluster {c}): {conteo[c]} contenedores")

# ------------------------------
# 5. Asignar nombres a las zonas (opcional: centroides)
# ------------------------------
# Calculamos centroides
centroides = kmeans.cluster_centers_
# Ordenar clusters por longitud (de oeste a este) o por latitud (de norte a sur)
# Para La Paz, podemos ordenar por longitud (oeste -68.12 a este -68.05)
orden = np.argsort(centroides[:, 0])   # Ordenar por longitud
mapeo_cluster_a_zona = {}
nombres_zonas = ["Centro", "Sopocachi", "Villa Fátima", "Achumani", "Obrajes"]  # Ajusta según tu criterio

for i, cluster_idx in enumerate(orden):
    mapeo_cluster_a_zona[cluster_idx] = i+1   # código de zona: 1..5

# Mapear al DataFrame
df['zona_codigo'] = df['cluster'].map(mapeo_cluster_a_zona)

# Contar por código de zona
conteo_final = df.groupby('zona_codigo').size().reset_index(name='num_contenedores')
conteo_final = conteo_final.sort_values('zona_codigo')

# Agregar nombre de zona (puedes personalizar según la ubicación geográfica)
# Para este ejemplo, asignamos nombres basados en el orden de los centroides
nombres = {}
for i, row in conteo_final.iterrows():
    cod = row['zona_codigo']
    nombres[cod] = nombres_zonas[cod-1]   # lista indexada desde 0
conteo_final['nombre_zona'] = conteo_final['zona_codigo'].map(nombres)

print("\nResultado final:")
print(conteo_final)

# ------------------------------
# 6. Guardar archivo CSV con el número de contenedores por zona
# ------------------------------
output_csv = "num_contenedores_por_zona.csv"
conteo_final.to_csv(output_csv, index=False)
print(f"\nArchivo guardado: {output_csv}")

# También puedes generar un CSV con todas las coordenadas y su asignación de zona
df_final = df[['longitud', 'latitud', 'zona_codigo']]
df_final.to_csv("contenedores_con_zona.csv", index=False)
print("Archivo con coordenadas y zona: contenedores_con_zona.csv")