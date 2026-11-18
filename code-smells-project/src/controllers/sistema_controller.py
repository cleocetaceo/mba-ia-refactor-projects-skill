"""Informações da API e health check."""
import logging
import sqlite3

from src.config.settings import Settings
from src.database import get_db
from src.middlewares.error_handler import HealthCheckError
from src.models import pedido_model, produto_model, usuario_model

logger = logging.getLogger(__name__)

ENDPOINTS_PUBLICOS = {
    "produtos": "/produtos",
    "usuarios": "/usuarios",
    "pedidos": "/pedidos",
    "login": "/login",
    "relatorios": "/relatorios/vendas",
    "health": "/health",
}


def info_api():
    return {
        "mensagem": "Bem-vindo à API da Loja",
        "versao": Settings.API_VERSION,
        "endpoints": dict(ENDPOINTS_PUBLICOS),
    }


def health_check():
    try:
        db = get_db()
        contagens = {
            "produtos": produto_model.contar(db),
            "usuarios": usuario_model.contar(db),
            "pedidos": pedido_model.contar(db),
        }
    except sqlite3.Error as err:
        logger.exception("Health check falhou")
        raise HealthCheckError("Banco de dados indisponível") from err

    return {
        "status": "ok",
        "database": "connected",
        "counts": contagens,
        "versao": Settings.API_VERSION,
        "ambiente": Settings.APP_ENV,
        "debug": Settings.DEBUG,
    }
