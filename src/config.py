from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///rentacar.db")

    # Paths
    VEHICLE_IMAGES_PATH = "data/vehicles/images/"
    VEHICLE_SPECS_PATH = "data/vehicles/specs/"
    DAMAGE_REPORTS_PATH = "data/vehicles/damage_reports/"

    # Model Configurations
    LLM_MODEL = "gpt-4o-mini"
    TEMPERATURE = 0.7
    MAX_TOKENS = 2000

    # Business Rules
    BUSINESS_HOURS = {
        "weekday": "09:00-18:00",
        "saturday": "09:00-13:00",
        "sunday": "closed"
    }