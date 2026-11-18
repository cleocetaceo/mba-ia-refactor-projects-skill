"""Casos de uso de produtos."""
import logging

from src.controllers import validators
from src.database import get_db
from src.middlewares.error_handler import NotFoundError
from src.models import produto_model

logger = logging.getLogger(__name__)

MSG_PRODUTO_NAO_ENCONTRADO = "Produto não encontrado"


def listar_produtos():
    produtos = produto_model.listar(get_db())
    logger.debug("Listando %d produtos", len(produtos))
    return produtos


def buscar_produto(produto_id):
    produto = produto_model.buscar_por_id(get_db(), produto_id)
    if not produto:
        raise NotFoundError(MSG_PRODUTO_NAO_ENCONTRADO, extra={"sucesso": False})
    return produto


def pesquisar_produtos(termo, categoria, preco_min, preco_max):
    return produto_model.pesquisar(
        get_db(),
        termo=termo,
        categoria=categoria,
        preco_min=validators.validar_filtro_preco(preco_min, "preco_min"),
        preco_max=validators.validar_filtro_preco(preco_max, "preco_max"),
    )


def criar_produto(dados):
    produto = validators.validar_produto(dados)
    produto_id = produto_model.criar(get_db(), **produto)
    logger.info("Produto criado com ID %s", produto_id)
    return {"id": produto_id}


def atualizar_produto(produto_id, dados):
    db = get_db()
    if not produto_model.buscar_por_id(db, produto_id):
        raise NotFoundError(MSG_PRODUTO_NAO_ENCONTRADO)
    produto = validators.validar_produto(dados)
    produto_model.atualizar(db, produto_id, **produto)
    logger.info("Produto %s atualizado", produto_id)


def deletar_produto(produto_id):
    db = get_db()
    if not produto_model.buscar_por_id(db, produto_id):
        raise NotFoundError(MSG_PRODUTO_NAO_ENCONTRADO)
    produto_model.desativar(db, produto_id)
    logger.info("Produto %s removido do catálogo", produto_id)
