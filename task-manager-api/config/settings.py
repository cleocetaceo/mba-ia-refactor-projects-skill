"""Configuração da aplicação lida de variáveis de ambiente, com defaults seguros para desenvolvimento."""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / '.env')


def _bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def _origins(value):
    if not value or value.strip() == '*':
        return '*'
    return [origin.strip() for origin in value.split(',') if origin.strip()]


class Settings:
    # Sem SECRET_KEY definida, gera uma chave aleatória por boot (nunca um literal no código).
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = _bool(os.environ.get('FLASK_DEBUG'))
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', '5000'))
    CORS_ORIGINS = _origins(os.environ.get('CORS_ORIGINS', '*'))
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()

    # Sem ADMIN_TOKEN, os endpoints administrativos ficam desabilitados (403).
    ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN') or None
    MIN_PASSWORD_LENGTH = int(os.environ.get('MIN_PASSWORD_LENGTH', '8'))
