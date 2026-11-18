"""Configuração da aplicação lida de variáveis de ambiente, com defaults seguros."""
import os
import secrets


def _bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _origins(value):
    if not value or value.strip() == "*":
        return "*"
    return [origin.strip() for origin in value.split(",") if origin.strip()]


class Settings:
    # Sem SECRET_KEY no ambiente, gera uma chave aleatória por boot (apenas desenvolvimento).
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _bool(os.environ.get("FLASK_DEBUG"))
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    # Sem ADMIN_TOKEN os endpoints administrativos ficam desabilitados (403).
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN") or None
    CORS_ORIGINS = _origins(os.environ.get("CORS_ORIGINS"))
    APP_ENV = os.environ.get("APP_ENV", "producao")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
    API_VERSION = "1.0.0"
