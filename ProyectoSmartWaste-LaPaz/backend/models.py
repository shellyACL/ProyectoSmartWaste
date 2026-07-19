from sqlalchemy import Column, Float, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry  
from database import Base
from sqlalchemy import Boolean
from sqlalchemy import ARRAY

class Zona(Base):
    __tablename__ = "zonas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String, nullable=True)
    contenedores = relationship("Contenedor", back_populates="zona")


class Contenedor(Base):
    __tablename__ = "contenedores"

    id = Column(Integer, primary_key=True, index=True)
    zona_id = Column(Integer, ForeignKey("zonas.id", ondelete="SET NULL"), nullable=True)
    codigo_qr = Column(String(50), unique=True, nullable=False, index=True)
     
    # Almacenamos un PUNTO geográfico con el sistema de coordenadas WGS84 (SRID 4326)
    # use_type_modifier=True ayuda a que SQLAlchemy entienda que es un subtipo específico
    ubicacion = Column(Geometry(geometry_type='POINT', srid=4326, spatial_index=True), nullable=False)
    
    estado_actual = Column(String(30), default="vacio", nullable=False)
    porcentaje_llenado_actual = Column(Integer, default=0, nullable=False)
    ultima_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())

    zona = relationship("Zona", back_populates="contenedores")

class ReporteQR(Base):
    __tablename__ = "reportes_qr"

    id = Column(Integer, primary_key=True, index=True)
    contenedor_id = Column(Integer, ForeignKey("contenedores.id", ondelete="CASCADE"), nullable=False)
    tipo_reporte = Column(String(50), nullable=False)
    comentario = Column(String, nullable=True)
    fecha_reporte = Column(DateTime, server_default=func.now())
    atendido = Column(Boolean, default=False, nullable=False)
    contenedor = relationship("Contenedor")

class Camion(Base):
    __tablename__ = "camiones"

    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String(20), unique=True, nullable=False)
    modelo = Column(String(50), nullable=True)
    capacidad_max_kg = Column(Float, default=5000.0) 
    estado = Column(String(20), default="disponible") 
    fecha_registro = Column(DateTime, server_default=func.now())

class Ruta(Base):
    __tablename__ = "rutas"

    id = Column(Integer, primary_key=True, index=True)
    camion_id = Column(Integer, ForeignKey("camiones.id", ondelete="RESTRICT"), nullable=False)
    orden_visita = Column(ARRAY(Integer), nullable=False)
    distancia_total_metros = Column(Float, nullable=False)
    tiempo_estimado_segundos = Column(Integer, nullable=False)
    estado_ruta = Column(String(20), default="pendiente") 
    fecha_creacion = Column(DateTime, server_default=func.now())