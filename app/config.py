import os
from pathlib import Path

from dotenv import load_dotenv

# Localiza o .env na raiz do backend
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    # Prioriza a URL do Neon no ambiente de produção.
    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://", "postgresql://", 1
        )

    # Mantém compatibilidade com a configuração local antiga.
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or (
        f"postgresql+psycopg2://"
        f"{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_HOST')}:"
        f"{os.getenv('POSTGRES_PORT')}/"
        f"{os.getenv('POSTGRES_DB')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Detecta conexões que tenham expirado.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
