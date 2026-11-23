"""Casos de uso administrativos (rotas protegidas por require_admin)."""
import logging
import re
import sqlite3

from src.database import get_db
from src.middlewares.error_handler import ValidationError
from src.models import admin_model

logger = logging.getLogger(__name__)

MSG_SOMENTE_SELECT = "Apenas uma sentença SELECT é permitida"

_LITERAL_TEXTO = re.compile(r"'(?:[^']|'')*'")
_INICIO_LEITURA = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)
_ESCRITA = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|DETACH|PRAGMA|VACUUM|REINDEX|REPLACE\s+INTO)\b",
    re.IGNORECASE,
)


def resetar_banco():
    db = get_db()
    with db:
        admin_model.limpar_tabelas(db)
    logger.warning("!!! BANCO DE DADOS RESETADO !!!")


def _validar_sentenca_leitura(dados):
    sql = dados.get("sql", "") if isinstance(dados, dict) else ""
    if not isinstance(sql, str) or not sql.strip():
        raise ValidationError("Query não informada")
    corpo = sql.strip().rstrip(";").strip()
    # Literais de texto são ignorados na análise para não confundir ';' ou palavras dentro de strings.
    sem_literais = _LITERAL_TEXTO.sub("''", corpo)
    if ";" in sem_literais or not _INICIO_LEITURA.match(sem_literais) or _ESCRITA.search(sem_literais):
        raise ValidationError(MSG_SOMENTE_SELECT)
    return corpo


def executar_query(dados):
    sql = _validar_sentenca_leitura(dados)
    try:
        return admin_model.consultar_somente_leitura(get_db(), sql)
    except sqlite3.Error as err:
        logger.warning("Query administrativa rejeitada: %s", err)
        raise ValidationError("Query inválida") from None
