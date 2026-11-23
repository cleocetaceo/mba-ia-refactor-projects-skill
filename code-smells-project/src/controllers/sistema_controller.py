"""Casos de uso de sistema: índice da API e health check."""
import logging
import sqlite3

from src.config import APP_VERSION
from src.database import get_db
from src.middlewares.error_handler import AppError
from src.models import sistema_model

logger = logging.getLogger(__name__)

MSG_BANCO_INDISPONIVEL = "Banco de dados indisponível"


def indice():
    return {
        "mensagem": "Bem-vindo à API da Loja",
        "versao": APP_VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }


def health(ambiente):
    try:
        counts = sistema_model.contar_registros(get_db())
    except sqlite3.Error:
        logger.exception("Health check falhou")
        raise AppError(
            MSG_BANCO_INDISPONIVEL,
            status_code=500,
            body={"status": "erro", "detalhes": MSG_BANCO_INDISPONIVEL},
        ) from None
    return {
        "status": "ok",
        "database": "connected",
        "counts": counts,
        "versao": APP_VERSION,
        "ambiente": ambiente,
    }
