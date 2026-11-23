"""Casos de uso de produtos."""
import logging

from src.controllers import validators
from src.database import get_db
from src.middlewares.error_handler import NotFoundError
from src.models import produto_model

logger = logging.getLogger(__name__)

MSG_NAO_ENCONTRADO = "Produto não encontrado"


def listar():
    produtos = produto_model.listar(get_db())
    logger.info("Listando %d produtos", len(produtos))
    return produtos


def buscar(termo, categoria, preco_min, preco_max):
    return produto_model.buscar(
        get_db(),
        termo or "",
        categoria or None,
        validators.validar_filtro_preco(preco_min, "preco_min"),
        validators.validar_filtro_preco(preco_max, "preco_max"),
    )


def obter(produto_id):
    produto = produto_model.buscar_por_id(get_db(), produto_id)
    if produto is None:
        raise NotFoundError(MSG_NAO_ENCONTRADO, include_sucesso=True)
    return produto


def criar(dados):
    campos = validators.validar_produto(dados)
    db = get_db()
    with db:
        produto_id = produto_model.criar(db, **campos)
    logger.info("Produto criado com ID %s", produto_id)
    return produto_id


def atualizar(produto_id, dados):
    db = get_db()
    if produto_model.buscar_por_id(db, produto_id) is None:
        raise NotFoundError(MSG_NAO_ENCONTRADO)
    campos = validators.validar_produto(dados)
    with db:
        produto_model.atualizar(db, produto_id, **campos)


def remover(produto_id):
    db = get_db()
    if produto_model.buscar_por_id(db, produto_id) is None:
        raise NotFoundError(MSG_NAO_ENCONTRADO)
    with db:
        produto_model.remover(db, produto_id)
    logger.info("Produto %s deletado", produto_id)
