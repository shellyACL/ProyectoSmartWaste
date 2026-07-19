from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ZonaCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class ZonaResponse(ZonaCreate):
    id: int

    class Config:
        from_attributes = True


class ContenedorCreate(BaseModel):
    zona_id: Optional[int] = None
    codigo_qr: str
    lat: float 
    lon: float  

class ContenedorResponse(BaseModel):
    id: int
    zona_id: Optional[int]
    codigo_qr: str
    estado_actual: str
    porcentaje_llenado_actual: int
    lat: float
    lon: float
    ultima_actualizacion: datetime

    class Config:
        from_attributes = True

# QR
class ReporteQRCreate(BaseModel):
    contenedor_id: int
    tipo_reporte: str  
    comentario: Optional[str] = None


class ReporteQRResponse(ReporteQRCreate):
    id: int
    fecha_reporte: datetime
    atendido: bool

    class Config:
        from_attributes = True

class RutaResponse(BaseModel):
    id: int
    camion_id: str
    orden_visita: list[int]
    distancia_total_metros: float
    tiempo_estimado_segundos: int
    estado_ruta: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True

class CamionCreate(BaseModel):
    placa: str
    modelo: Optional[str] = None
    capacidad_max_kg: Optional[float] = 5000.0

class CamionResponse(CamionCreate):
    id: int
    estado: str
    fecha_registro: datetime

    class Config:
        from_attributes = True