"""Casos de uso administrativos (rotas protegidas por require_admin)."""
import logging
import sqlite3

from src.database import get_db, transaction
from src.middlewares.error_handler import AppError, ValidationError
from src.models import admin_model

logger = logging.getLogger(__name__)


def resetar_banco():
    db = get_db()
    with transaction(db):
        admin_model.limpar_tabelas(db)
    logger.warning("Banco de dados resetado via endpoint administrativo")


def executar_query(dados):
    sql = dados.get("sql", "") if isinstance(dados, dict) else ""
    if not isinstance(sql, str) or not sql.strip():
        raise ValidationError("Query não informada")

    db = get_db()
    logger.warning("Query administrativa executada")
    try:
        if sql.strip().upper().startswith("SELECT"):
            return {"dados": admin_model.consultar(db, sql)}
        with transaction(db):
            admin_model.executar(db, sql)
        return {"mensagem": "Query executada"}
    except sqlite3.Error as err:
        # Endpoint restrito a administradores: a mensagem do SQLite ajuda a corrigir a query.
        raise AppError(str(err), status_code=500) from err
