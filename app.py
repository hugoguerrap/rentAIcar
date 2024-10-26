import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.agents.rentacar_agent import RentaCarAgent
from src.learning.response_optimizer import ResponseOptimizer
from src.database.models import Base

# Configuración de la base de datos
DATABASE_URL = "sqlite:///./test.db"  # Cambia esto a tu URL de base de datos
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Inicializar el agente y el optimizador de respuestas
session = SessionLocal()
response_optimizer = ResponseOptimizer(session)
agent = RentaCarAgent(session, response_optimizer)

# Configuración de la aplicación Streamlit
st.title("Agente de Atención al Cliente - RentACar")

# Entrada de texto para la consulta del usuario
query = st.text_input("Introduce tu consulta:")

# Botón para enviar la consulta
if st.button("Enviar"):
    if query:
        # Procesar la consulta con el agente
        result = agent.process_query(query)

        # Mostrar la respuesta del agente
        st.write("**Respuesta del Agente:**")
        st.write(result.get('response', 'No se pudo obtener una respuesta.'))

        # Mostrar el contexto utilizado si está disponible
        if 'context' in result:
            st.write("**Contexto Utilizado:**")
            st.json(result['context'])
        else:
            st.write("No se pudo obtener el contexto.")

        # Entrada de feedback del usuario
        feedback_score = st.slider("Puntuación del Feedback (0-5):", 0.0, 5.0, 3.0)
        feedback_comments = st.text_area("Comentarios del Feedback:")

        # Botón para enviar el feedback
        if st.button("Enviar Feedback"):
            interaction_id = result.get('interaction_id')
            if interaction_id is not None:
                feedback_processed = agent.process_feedback(interaction_id, feedback_score, feedback_comments)
                if feedback_processed:
                    st.success("Feedback procesado correctamente.")
                else:
                    st.error("Error al procesar el feedback.")
            else:
                st.error("No se pudo obtener el ID de la interacción.")
    else:
        st.error("Por favor, introduce una consulta.")