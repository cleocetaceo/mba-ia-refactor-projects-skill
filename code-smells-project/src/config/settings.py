"""Configuração da aplicação, lida de variáveis de ambiente com defaults seguros.

Todas as variáveis estão documentadas em .env.example.
"""
import os
import secrets

APP_VERSION = "1.0.0"


def _bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    # Sem SECRET_KEY no ambiente, gera uma chave aleatória a cada boot (adequado para dev).
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _bool(os.environ.get("FLASK_DEBUG"))
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    # Sem ADMIN_TOKEN, os endpoints administrativos ficam desabilitados (403).
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN") or None
    APP_ENV = os.environ.get("APP_ENV", "producao")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
