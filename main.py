from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from src.agents.rentacar_agent import RentaCarAgent
from src.database.models import Base
from src.learning.response_optimizer import ResponseOptimizer

# Configuración de la base de datos
DATABASE_URL = "sqlite:///rentacar.db"  # Puedes cambiar esto según tu configuración
engine = create_engine(DATABASE_URL)

# Crear todas las tablas
Base.metadata.create_all(engine)

# Crear fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def main():
    # Crear una nueva sesión
    session = SessionLocal()

    try:
        # Inicializar componentes
        optimizer = ResponseOptimizer(session)
        agent = RentaCarAgent(session, optimizer)

        # Procesar una consulta
        result = await agent.process_query(
            "¿Cuánto cuesta alquilar un SUV para el fin de semana?",
            additional_context={
                'season': 'high_season',
                'vehicle_type': 'SUV',
                'price_range': 'medium'
            }
        )

        print("Respuesta:", result)  # Para ver la respuesta

        # Simular feedback del cliente
        if 'interaction_id' in result:
            feedback_result = await agent.process_feedback(
                interaction_id=result['interaction_id'],
                feedback_score=4.5,
                comments="Respuesta clara y precisa"
            )
            print("Feedback procesado:", feedback_result)

    except Exception as e:
        print(f"Error en la ejecución: {str(e)}")
        session.rollback()
        raise e
    finally:
        # Cerrar la sesión al finalizar
        session.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())