from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from datetime import datetime, timedelta

from src.database.models import ResponseTemplate, Interaction


class ResponseOptimizer:
    def __init__(self, session):
        self.session = session
        self.vectorizer = TfidfVectorizer()

    def analyze_query(self, query: str, context: dict):
        """Analiza la consulta y determina la mejor plantilla de respuesta basada en el histórico"""
        # Vectorizar la consulta
        query_vector = self.vectorizer.fit_transform([query])

        # Obtener interacciones exitosas recientes
        successful_interactions = self.session.query(Interaction) \
            .filter(Interaction.feedback_score >= 4.0) \
            .filter(Interaction.timestamp >= datetime.now() - timedelta(days=30)) \
            .all()

        best_template = None
        best_score = 0

        for interaction in successful_interactions:
            # Calcular similitud de la consulta
            similarity = cosine_similarity(
                query_vector,
                self.vectorizer.transform([interaction.query])
            )[0][0]

            # Calcular similitud del contexto
            context_score = self.calculate_context_similarity(
                context,
                interaction.context
            )

            # Combinar puntuaciones
            combined_score = similarity * 0.7 + context_score * 0.3

            if combined_score > best_score:
                best_score = combined_score
                best_template = interaction.template

        return best_template

    def update_template_metrics(self, template_id: int, feedback_score: float):
        """Actualiza las métricas de la plantilla basado en el feedback"""
        template = self.session.query(ResponseTemplate).get(template_id)

        # Actualizar promedios
        template.use_count += 1
        template.average_feedback = (
                (template.average_feedback * (template.use_count - 1) + feedback_score)
                / template.use_count
        )
        template.last_updated = datetime.utcnow()

        # Actualizar tasa de éxito
        if feedback_score >= 4.0:
            template.success_rate = (
                    (template.success_rate * (template.use_count - 1) + 1)
                    / template.use_count
            )

        self.session.commit()

    def calculate_context_similarity(self, context1: dict, context2: dict):
        """Calcula la similitud entre dos contextos"""
        # Implementar lógica específica para RentaCar
        similarity_score = 0
        total_weights = 0

        # Comparar tipo de vehículo (peso: 0.4)
        if context1.get('vehicle_type') == context2.get('vehicle_type'):
            similarity_score += 0.4
        total_weights += 0.4

        # Comparar rango de precio (peso: 0.3)
        price_similarity = self.compare_price_ranges(
            context1.get('price_range'),
            context2.get('price_range')
        )
        similarity_score += price_similarity * 0.3
        total_weights += 0.3

        # Comparar temporada (peso: 0.3)
        if context1.get('season') == context2.get('season'):
            similarity_score += 0.3
        total_weights += 0.3

        return similarity_score / total_weights if total_weights > 0 else 0