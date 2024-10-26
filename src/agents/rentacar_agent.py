from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from src.context.context_builder import ContextBuilder
from src.database.models import Interaction


class RentaCarAgent:
    def __init__(self, session: Session, response_optimizer):
        self.session = session
        self.optimizer = response_optimizer
        self.context_builder = ContextBuilder()
        self.llm = ChatOpenAI(temperature=0.7)

    async def process_query(self, query: str, additional_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesa una consulta y genera una respuesta contextualizada
        """
        try:
            # Construir contexto
            context = self.context_builder.build_context(query, additional_context)

            # Categorizar la consulta
            category = self.categorize_query(query)

            # Obtener la mejor plantilla basada en el histórico
            template = self.optimizer.analyze_query(query, context)

            # Si no hay plantilla, crear una respuesta nueva
            if not template:
                response = await self._generate_new_response(query, category, context)
            else:
                response = await self._apply_template(template, context)

            # Registrar la interacción
            interaction = await self._record_interaction(query, response, category, context, template)

            return {
                'response': response,
                'interaction_id': interaction.id,
                'category': category,
                'context': context
            }

        except Exception as e:
            print(f"Error processing query: {str(e)}")
            # Respuesta de fallback en caso de error
            return {
                'response': "Lo siento, estoy teniendo problemas para procesar tu consulta. ¿Podrías reformularla?",
                'error': str(e)
            }

    async def _generate_new_response(self, query: str, category: str, context: Dict[str, Any]) -> str:
        """
        Genera una nueva respuesta cuando no hay plantilla disponible
        """
        # Definir prompts específicos por categoría
        category_prompts = {
            'vehicle_info': """Eres un experto asesor de RentaCar. 
            Proporciona información detallada sobre el vehículo solicitado.
            Contexto del vehículo: {context}
            Consulta: {query}
            Responde de manera profesional y detallada.""",

            'pricing': """Eres un asesor de ventas de RentaCar.
            Proporciona información clara sobre precios y condiciones.
            Contexto de la cotización: {context}
            Consulta: {query}
            Incluye información sobre tarifas, seguros y servicios adicionales.""",

            'booking': """Eres un agente de reservas de RentaCar.
            Ayuda al cliente con su reserva de vehículo.
            Contexto de la reserva: {context}
            Consulta: {query}
            Guía al cliente en el proceso de reserva.""",

            'damage': """Eres un especialista en evaluación de daños de RentaCar.
            Analiza y responde consultas sobre daños en vehículos.
            Contexto del incidente: {context}
            Consulta: {query}
            Proporciona información clara sobre el proceso de reporte de daños.""",

            'claims': """Eres un agente de atención al cliente de RentaCar.
            Atiende los reclamos y quejas de manera profesional.
            Contexto del reclamo: {context}
            Consulta: {query}
            Ofrece soluciones y alternativas al cliente."""
        }

        # Obtener el prompt adecuado para la categoría
        prompt_template = category_prompts.get(
            category,
            "Eres un asistente de RentaCar. Responde la siguiente consulta: {query}"
        )

        # Crear el prompt
        prompt = ChatPromptTemplate.from_template(prompt_template)

        # Generar la respuesta
        response = await self.llm.agenerate([prompt.format_messages(
            query=query,
            context=str(context)
        )])

        return response.generations[0][0].text

    async def _apply_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Aplica una plantilla existente con el contexto actual
        """
        try:
            # Reemplazar placeholders en la plantilla
            response = template.template.format(**context)
            return response
        except KeyError:
            # Si hay error con la plantilla, generar respuesta nueva
            return await self._generate_new_response(
                query="",  # Query vacío porque estamos usando el contexto
                category=template.category.name,
                context=context
            )

    async def _record_interaction(self, query: str, response: str,
                                  category: str, context: Dict[str, Any],
                                  template: Any = None) -> Any:
        """
        Registra la interacción en la base de datos
        """
        interaction = Interaction(
            query=query,
            response=response,
            category_id=category,
            template_id=template.id if template else None,
            context=context,
            timestamp=datetime.utcnow()
        )

        self.session.add(interaction)
        await self.session.flush()
        await self.session.commit()

        return interaction

    async def process_feedback(self, interaction_id: int,
                               feedback_score: float,
                               comments: str = None) -> bool:
        """
        Procesa el feedback de una interacción
        """
        try:
            interaction = await self.session.get(Interaction, interaction_id)
            if not interaction:
                return False

            # Actualizar la interacción con el feedback
            interaction.feedback_score = feedback_score
            interaction.feedback_comments = comments

            # Actualizar métricas de la plantilla si existe
            if interaction.template_id:
                await self.optimizer.update_template_metrics(
                    interaction.template_id,
                    feedback_score
                )

            # Analizar indicadores de éxito
            success_indicators = self._analyze_success_indicators(interaction)
            interaction.success_indicators = success_indicators

            await self.session.commit()
            return True

        except Exception as e:
            print(f"Error processing feedback: {str(e)}")
            return False

    def _analyze_success_indicators(self, interaction: Any) -> Dict[str, Any]:
        """
        Analiza indicadores de éxito de la interacción
        """
        return {
            'response_time': (datetime.utcnow() - interaction.timestamp).total_seconds(),
            'led_to_booking': 'reserva' in interaction.response.lower(),
            'required_followup': False,  # Por defecto
            'sentiment_score': self._analyze_sentiment(interaction.response),
            'complexity_level': self._calculate_complexity(interaction.query, interaction.response)
        }

    def _analyze_sentiment(self, text: str) -> float:
        """
        Analiza el sentimiento de un texto (implementación básica)
        """
        positive_words = ['gracias', 'excelente', 'perfecto', 'genial', 'ayuda']
        negative_words = ['problema', 'error', 'mal', 'queja', 'insatisfecho']

        text = text.lower()
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        total = positive_count + negative_count
        if total == 0:
            return 0.5

        return positive_count / total

    def _calculate_complexity(self, query: str, response: str) -> str:
        """
        Calcula la complejidad de la interacción
        """
        query_length = len(query.split())
        response_length = len(response.split())

        if response_length < 20:
            return 'simple'
        elif response_length < 50:
            return 'medium'
        else:
            return 'complex'