import os
import cv2
import models
import schemas
import numpy as np

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_X, ST_Y  
from vision_service import VisionService
from datetime import datetime
from router_service import OSRMService
from database import engine, Base, get_db
from prediction_service import PredictionService
from router_service import OSRMService

osrm_servicio = OSRMService()
vision_servicio = VisionService()

with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
    conn.commit()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SmartWaste API",
    description="Sistema Inteligente de Gestión de Residuos Urbanos",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "status": "online",
        "proyecto": "SmartWaste La Paz",
        "mensaje": "¡El backend está vivo y conectado a PostGIS! Hola Mundo:D"
    }

# ============================================================
# ENDPOINTS PARA ZONAS
# ============================================================

@app.post("/zonas/", response_model=schemas.ZonaResponse, tags=["Zonas"])
def crear_zona(zona: schemas.ZonaCreate, db: Session = Depends(get_db)):
    nueva_zona = models.Zona(nombre=zona.nombre, descripcion=zona.descripcion)
    db.add(nueva_zona)
    db.commit()
    db.refresh(nueva_zona)
    return nueva_zona

# ============================================================
# ENDPOINTS PARA CAMIONES
# ============================================================

@app.post("/camiones/", response_model=schemas.CamionResponse, tags=["Gestión de Flota"])
def registrar_camion(camion: schemas.CamionCreate, db: Session = Depends(get_db)):
    db_camion = db.query(models.Camion).filter(models.Camion.placa == camion.placa).first()
    if db_camion:
        raise HTTPException(status_code=400, detail="Esta placa ya está registrada en el sistema.")
        
    nuevo_camion = models.Camion(
        placa=camion.placa,
        modelo=camion.modelo,
        capacidad_max_kg=camion.capacidad_max_kg
    )
    db.add(nuevo_camion)
    db.commit()
    db.refresh(nuevo_camion)
    return nuevo_camion

# ============================================================
# ENDPOINTS PARA CONTENEDORES
# ============================================================

@app.post("/contenedores/", response_model=schemas.ContenedorResponse, tags=["Contenedores"])
def crear_contenedor(contenedor: schemas.ContenedorCreate, db: Session = Depends(get_db)):
    # Validar si el código QR ya existe para evitar duplicados
    db_contenedor = db.query(models.Contenedor).filter(models.Contenedor.codigo_qr == contenedor.codigo_qr).first()
    if db_contenedor:
        raise HTTPException(status_code=400, detail="El código QR ya está registrado en otro contenedor.")

    # Convertir Lat y Lon flotantes en un punto geográfico (PostGIS)
    punto_geografico = func.ST_SetSRID(func.ST_MakePoint(contenedor.lon, contenedor.lat), 4326)

    nuevo_contenedor = models.Contenedor(
        zona_id=contenedor.zona_id,
        codigo_qr=contenedor.codigo_qr,
        ubicacion=punto_geografico,
        estado_actual="vacio",
        porcentaje_llenado_actual=0
    )
    
    db.add(nuevo_contenedor)
    db.commit()
    db.refresh(nuevo_contenedor)
    
    return schemas.ContenedorResponse(
        id=nuevo_contenedor.id,
        zona_id=nuevo_contenedor.zona_id,
        codigo_qr=nuevo_contenedor.codigo_qr,
        estado_actual=nuevo_contenedor.estado_actual,
        porcentaje_llenado_actual=nuevo_contenedor.porcentaje_llenado_actual,
        lat=contenedor.lat,
        lon=contenedor.lon,
        ultima_actualizacion=nuevo_contenedor.ultima_actualizacion
    )

@app.get("/contenedores/", response_model=list[schemas.ContenedorResponse], tags=["Contenedores"])
def listar_contenedores(db: Session = Depends(get_db)):
    resultados = db.query(
        models.Contenedor.id,
        models.Contenedor.zona_id,
        models.Contenedor.codigo_qr,
        models.Contenedor.estado_actual,
        models.Contenedor.porcentaje_llenado_actual,
        models.Contenedor.ultima_actualizacion,
        ST_X(models.Contenedor.ubicacion).label("lon"),
        ST_Y(models.Contenedor.ubicacion).label("lat")
    ).all()

    lista_respuesta = []
    for r in resultados:
        lista_respuesta.append(
            schemas.ContenedorResponse(
                id=r.id,
                zona_id=r.zona_id,
                codigo_qr=r.codigo_qr,
                estado_actual=r.estado_actual,
                porcentaje_llenado_actual=r.porcentaje_llenado_actual,
                lat=r.lat,
                lon=r.lon,
                ultima_actualizacion=r.ultima_actualizacion
            )
        )
    return lista_respuesta

# ============================================================
# ENDPOINTS PARA RUTAS
# ============================================================
@app.get("/rutas/calcular-distancia-prueba/", tags=["Rutas de Recolección"])
def probar_ruta_real(lat_inicio: float, lon_inicio: float, lat_fin: float, lon_fin: float):
    """
    Calcula la distancia y tiempo real entre dos puntos de la ciudad usando calles reales.
    """
    resultado = osrm_servicio.calcular_ruta_real([(lat_inicio, lon_inicio), (lat_fin, lon_fin)])
    
    if not resultado["exito"]:
        raise HTTPException(status_code=500, detail=resultado["error"])
        
    return {
        "mensaje": "Cálculo de ruta real exitoso",
        "distancia_km": resultado["distancia_metros"] / 1000, 
        "tiempo_minutos": resultado["tiempo_segundos"] / 60   
    }

@app.post("/vision/analizar-camara/{contenedor_id}/", tags=["Computer Vision"])
def analizar_foto_contenedor(contenedor_id: int, db: Session = Depends(get_db)):
    """
    Simula la recepción de una imagen desde una cámara IoT para un contenedor específico.
    Procesa la imagen, determina el nivel de llenado y actualiza la base de datos en tiempo real.
    """
    contenedor = db.query(models.Contenedor).filter(models.Contenedor.id == contenedor_id).first()
    if not contenedor:
        raise HTTPException(status_code=404, detail="Contenedor no encontrado.")

    ruta_ficticia = "test_contenedor.jpg"
    imagen_vacia = np.zeros((640, 640, 3), dtype=np.uint8)
    cv2.imwrite(ruta_ficticia, imagen_vacia)

    resultado_ia = vision_servicio.procesar_y_analizar_imagen(ruta_ficticia)
    
    if os.path.exists(ruta_ficticia):
        os.remove(ruta_ficticia)

    if not resultado_ia["exito"]:
        raise HTTPException(status_code=500, detail=resultado_ia["error"])

    nuevo_estado = resultado_ia["estado_detectado"]
    contenedor.estado_actual = nuevo_estado
    mapeo_porcentajes = {"vacio": 0, "medio": 40, "casi_lleno": 75, "lleno": 95, "desbordado": 100}
    contenedor.porcentaje_llenado_actual = mapeo_porcentajes[nuevo_estado]
    
    db.commit()
    db.refresh(contenedor)

    return {
        "mensaje": "Análisis de visión completado y estado actualizado",
        "contenedor_id": contenedor.id,
        "codigo_qr": contenedor.codigo_qr,
        "vision_valida": {
            "estado_detectado": nuevo_estado,
            "confianza": resultado_ia["confianza"],
            "porcentaje_estimado": contenedor.porcentaje_llenado_actual
        },
        "estado_actual_db": contenedor.estado_actual
    }

@app.post("/reportes-qr/", response_model=schemas.ReporteQRResponse, tags=["Reportes QR Ciudadanos"])
def crear_reporte_ciudadano(reporte: schemas.ReporteQRCreate, db: Session = Depends(get_db)):
    """
    Registra un reporte ciudadano mediante QR.
    Si el reporte es crítico ('emergencia' o 'contenedor_lleno'), altera la prioridad del contenedor en la DB.
    """
    contenedor = db.query(models.Contenedor).filter(models.Contenedor.id == reporte.contenedor_id).first()
    if not contenedor:
        raise HTTPException(status_code=404, detail="El contenedor escaneado no existe.")

    tipos_validos = ['contenedor_lleno', 'basura_alrededor', 'contenedor_roto', 'emergencia']
    if reporte.tipo_reporte not in tipos_validos:
        raise HTTPException(status_code=400, detail=f"Tipo de reporte inválido. Use uno de: {tipos_validos}")

    nuevo_reporte = models.ReporteQR(
        contenedor_id=reporte.contenedor_id,
        tipo_reporte=reporte.tipo_reporte,
        comentario=reporte.comentario
    )
    db.add(nuevo_reporte)

    if reporte.tipo_reporte == 'emergencia':
        contenedor.estado_actual = 'roto'
        contenedor.porcentaje_llenado_actual = 100 
    elif reporte.tipo_reporte == 'contenedor_lleno' or reporte.tipo_reporte == 'basura_alrededor':
        contenedor.estado_actual = 'desbordado'
        contenedor.porcentaje_llenado_actual = 100

    db.commit()
    db.refresh(nuevo_reporte)

    return nuevo_reporte



GARAJE_ACHUMANI = (-16.535331, -68.074350)
RELLENO_SAKA_CHURU = (-16.555393, -68.131637)

ia_servicio = PredictionService()

@app.post("/rutas/generar-hoja-ruta/", response_model=schemas.RutaResponse, tags=["Rutas de Recolección"])
def generar_ruta_del_dia(camion_id: int, db: Session = Depends(get_db)):
    """
    Verifica que el camión exista en la BD, evalúa los contenedores usando 
    TensorFlow, YOLO o QR, calcula la ruta vial y la guarda en la tabla 'rutas'.
    """

    camion = db.query(models.Camion).filter(models.Camion.id == camion_id).first()
    if not camion:
        raise HTTPException(status_code=404, detail="El camión asignado no existe en la flota de la BD.")
    if camion.estado == "mantenimiento":
        raise HTTPException(status_code=400, detail="Este camión está en el taller mecánico, elige otro.")

    contenedores = db.query(
        models.Contenedor.id,
        models.Contenedor.codigo_qr,
        models.Contenedor.estado_actual,
        models.Contenedor.porcentaje_llenado_actual,
        ST_X(models.Contenedor.ubicacion).label("lon"),
        ST_Y(models.Contenedor.ubicacion).label("lat")
    ).all()
    
    puntos_a_recolectar = [GARAJE_ACHUMANI]
    ids_contenedores_orden_original = []
    
    for c in contenedores:
        es_critico = (c.estado_actual in ['lleno', 'desbordado', 'roto'] or c.porcentaje_llenado_actual >= 70)
        
        if not es_critico:
            datos_ia = {"zona": 1, "llenado_ayer": c.porcentaje_llenado_actual, "dia_semana_mañana": 2, "feria_ayer": 0, "num_contenedores": 10, "topografia": 1, "clima_mañana": 0, "bloqueo_ayer": 0}
            if ia_servicio.predecir_llenado(datos_ia) >= 70.0:
                es_critico = True
        
        if es_critico:
            puntos_a_recolectar.append((c.lat, c.lon))
            ids_contenedores_orden_original.append(c.id)

    if len(puntos_a_recolectar) == 1: 
        raise HTTPException(status_code=400, detail="No hay contenedores críticos hoy. Flota en espera.")

    puntos_a_recolectar.append(RELLENO_SAKA_CHURU)

    resultado_osrm = osrm_servicio.optimizar_viaje_multiples_puntos(puntos_a_recolectar)
    if not resultado_osrm["exito"]:
        raise HTTPException(status_code=500, detail=resultado_osrm["error"])

    orden_indices = resultado_osrm["orden_visita_optimo"]
    orden_visita_final_ids = []
    for idx in orden_indices:
        if idx != 0 and idx != (len(puntos_a_recolectar) - 1):
            orden_visita_final_ids.append(ids_contenedores_orden_original[idx - 1])

    nueva_ruta = models.Ruta(
        camion_id=camion.id, 
        orden_visita=orden_visita_final_ids,
        distancia_total_metros=resultado_osrm["distancia_total_km"] * 1000,
        tiempo_estimado_segundos=int(resultado_osrm["tiempo_total_minutos"] * 60),
        estado_ruta="pendiente"
    )
    camion.estado = "en_ruta"
    
    db.add(nueva_ruta)
    db.commit()
    db.refresh(nueva_ruta)

    return nueva_ruta

