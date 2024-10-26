# src/context/context_builder.py

from typing import Dict, Any
from datetime import datetime
import re
from enum import Enum

class VehicleType(Enum):
    COMPACT = "compact"
    SEDAN = "sedan"
    SUV = "suv"
    LUXURY = "luxury"
    VAN = "van"

class Season(Enum):
    LOW = "low_season"
    MEDIUM = "medium_season"
    HIGH = "high_season"

class PriceRange(Enum):
    ECONOMIC = "economic"
    MEDIUM = "medium"
    PREMIUM = "premium"

class ContextBuilder:
    def __init__(self):
        # Palabras clave para identificar contextos específicos de RentaCar
        self.vehicle_keywords = {
            VehicleType.COMPACT: ["compacto", "pequeño", "económico", "city car"],
            VehicleType.SEDAN: ["sedan", "mediano", "familiar"],
            VehicleType.SUV: ["suv", "todoterreno", "4x4", "camioneta"],
            VehicleType.LUXURY: ["lujo", "premium", "alta gama"],
            VehicleType.VAN: ["van", "furgoneta", "minivan"]
        }

        self.price_keywords = {
            PriceRange.ECONOMIC: ["económico", "barato", "bajo costo"],
            PriceRange.MEDIUM: ["medio", "estándar", "normal"],
            PriceRange.PREMIUM: ["premium", "caro", "alto"]
        }

        # Definir temporadas
        self.season_dates = {
            Season.HIGH: [(12, 15, 1, 31),  # Verano
                         (7, 1, 7, 31)],    # Vacaciones de invierno
            Season.MEDIUM: [(11, 1, 12, 14),
                          (2, 1, 2, 28)],
            Season.LOW: [(3, 1, 6, 30),
                        (8, 1, 10, 31)]
        }

    def build_context(self, query: str, additional_context: Dict[str, Any] = None) -> Dict[str, Any]:
        context = {
            'timestamp': datetime.now(),
            'vehicle_type': self._detect_vehicle_type(query),
            'price_range': self._detect_price_range(query),
            'season': self._get_current_season(),
            'is_weekend': self._is_weekend(),
            'query_intent': self._detect_intent(query),
            'location_info': self._extract_location(query),
            'duration_info': self._extract_duration(query),
            'special_requirements': self._extract_special_requirements(query)
        }

        if additional_context:
            context.update(additional_context)

        return context


    def _detect_vehicle_type(self, query: str) -> VehicleType:
        """
        Detecta el tipo de vehículo mencionado en la consulta
        """
        query = query.lower()
        for vehicle_type, keywords in self.vehicle_keywords.items():
            if any(keyword in query for keyword in keywords):
                return vehicle_type
        return None

    def _detect_price_range(self, query: str) -> PriceRange:
        """
        Detecta el rango de precio mencionado en la consulta
        """
        query = query.lower()
        for price_range, keywords in self.price_keywords.items():
            if any(keyword in query for keyword in keywords):
                return price_range
        return PriceRange.MEDIUM  # Default a rango medio

    def _get_current_season(self) -> Season:
        """
        Determina la temporada actual basada en la fecha
        """
        current_date = datetime.now()
        month, day = current_date.month, current_date.day

        for season, date_ranges in self.season_dates.items():
            for start_month, start_day, end_month, end_day in date_ranges:
                if self._is_date_in_range(month, day, start_month, start_day, end_month, end_day):
                    return season
        return Season.LOW

    def _detect_intent(self, query: str) -> str:
        """
        Detecta la intención principal de la consulta
        """
        intents = {
            'cotización': ['precio', 'costo', 'tarifa', 'cuánto cuesta'],
            'reserva': ['reservar', 'alquilar', 'rentar', 'disponible'],
            'información': ['características', 'especificaciones', 'tiene'],
            'reclamo': ['problema', 'queja', 'reclamo', 'mal'],
            'daños': ['daño', 'golpe', 'accidente', 'rayón']
        }

        query = query.lower()
        for intent, keywords in intents.items():
            if any(keyword in query for keyword in keywords):
                return intent
        return 'información'  # Intent por defecto

    def _extract_location(self, query: str) -> Dict[str, str]:
        """
        Extrae información de ubicación de la consulta
        """
        location_info = {
            'pickup_location': None,
            'return_location': None
        }

        # Patrones para detectar ubicaciones
        pickup_patterns = [
            r'retirar en (.+?)(?=\s+y|\s+hasta|$)',
            r'desde (.+?)(?=\s+hasta|$)'
        ]
        return_patterns = [
            r'devolver en (.+?)(?=\s+y|\s+desde|$)',
            r'hasta (.+?)(?=\s+desde|$)'
        ]

        for pattern in pickup_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                location_info['pickup_location'] = match.group(1).strip()
                break

        for pattern in return_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                location_info['return_location'] = match.group(1).strip()
                break

        return location_info

    def _extract_duration(self, query: str) -> Dict[str, Any]:
        """
        Extrae información sobre la duración del alquiler
        """
        duration_info = {
            'start_date': None,
            'end_date': None,
            'duration_days': None
        }

        # Patrones para detectar duración
        duration_patterns = [
            r'(\d+)\s*(?:día|dias|día)',
            r'(\d+)\s*(?:semana|semanas)',
            r'(\d+)\s*(?:mes|meses)'
        ]

        for pattern in duration_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                number = int(match.group(1))
                if 'día' in pattern:
                    duration_info['duration_days'] = number
                elif 'semana' in pattern:
                    duration_info['duration_days'] = number * 7
                elif 'mes' in pattern:
                    duration_info['duration_days'] = number * 30

        return duration_info

    def _extract_special_requirements(self, query: str) -> Dict[str, bool]:
        """
        Extrae requerimientos especiales mencionados en la consulta
        """
        requirements = {
            'gps': False,
            'child_seat': False,
            'additional_driver': False,
            'insurance': False,
            'automatic': False
        }

        requirement_keywords = {
            'gps': ['gps', 'navegador', 'navegación'],
            'child_seat': ['silla', 'asiento', 'niño', 'bebé'],
            'additional_driver': ['conductor adicional', 'segundo conductor'],
            'insurance': ['seguro', 'cobertura'],
            'automatic': ['automático', 'automática']
        }

        query = query.lower()
        for req, keywords in requirement_keywords.items():
            if any(keyword in query for keyword in keywords):
                requirements[req] = True

        return requirements

    def _is_weekend(self) -> bool:
        """
        Determina si la fecha actual es fin de semana
        """
        return datetime.now().weekday() >= 5

    def _is_date_in_range(self, current_month, current_day,
                         start_month, start_day, end_month, end_day) -> bool:
        """
        Determina si una fecha está dentro de un rango específico
        """
        current = current_month * 100 + current_day
        start = start_month * 100 + start_day
        end = end_month * 100 + end_day

        if start <= end:
            return start <= current <= end
        else:  # Para rangos que cruzan el año
            return current >= start or current <= end