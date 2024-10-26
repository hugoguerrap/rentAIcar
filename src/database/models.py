from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class QueryCategory(Base):
    __tablename__ = 'query_categories'

    id = Column(Integer, primary_key=True)
    name = Column(String)  # vehicle_info, damage_assessment, booking, claims, etc.
    description = Column(String)
    success_patterns = Column(JSON)  # Patrones de respuestas exitosas


class ResponseTemplate(Base):
    __tablename__ = 'response_templates'

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('query_categories.id'))
    template = Column(String)
    context_pattern = Column(String)  # Patrón de contexto donde esta respuesta funciona mejor
    success_rate = Column(Float, default=0.0)
    use_count = Column(Integer, default=0)
    average_feedback = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)

    category = relationship("QueryCategory")


class Interaction(Base):
    __tablename__ = 'interactions'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    query = Column(String)
    response = Column(String)
    category_id = Column(Integer, ForeignKey('query_categories.id'))
    template_id = Column(Integer, ForeignKey('response_templates.id'))
    context = Column(JSON)  # Almacena el contexto de la consulta
    feedback_score = Column(Float)
    feedback_comments = Column(String)
    success_indicators = Column(JSON)  # Métricas de éxito específicas

    category = relationship("QueryCategory")
    template = relationship("ResponseTemplate")