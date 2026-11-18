"""Casos de uso de pedidos."""
import logging
from collections import Counter

from src.controllers import validators
from src.database import get_db, transaction
from src.middlewares.error_handler import AppError, NotFoundError
from src.models import pedido_model, produto_model, usuario_model
from src.services import notification_service

logger = logging.getLogger(__name__)


class PedidoRecusadoError(AppError):
    """Pedido rejeitado por regra de negócio (mesmo formato de erro da API original)."""

    status_code = 400

    def __init__(self, message):
        super().__init__(message, extra={"sucesso": False})


def criar_pedido(dados):
    usuario_id, itens = validators.validar_pedido(dados)
    db = get_db()

    with transaction(db):
        if not usuario_model.existe(db, usuario_id):
            raise PedidoRecusadoError(f"Usuário {usuario_id} não encontrado")

        produtos = produto_model.buscar_por_ids(db, (item["produto_id"] for item in itens))
        quantidade_por_produto = Counter()
        for item in itens:
            quantidade_por_produto[item["produto_id"]] += item["quantidade"]

        total = 0
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise PedidoRecusadoError(f"Produto {item['produto_id']} não encontrado")
            if produto["estoque"] < quantidade_por_produto[item["produto_id"]]:
                raise PedidoRecusadoError("Estoque insuficiente para " + produto["nome"])
            total = total + (produto["preco"] * item["quantidade"])

        pedido_id = pedido_model.inserir(db, usuario_id, total)
        for item in itens:
            produto = produtos[item["produto_id"]]
            pedido_model.inserir_item(db, pedido_id, item["produto_id"], item["quantidade"], produto["preco"])
            if not produto_model.baixar_estoque(db, item["produto_id"], item["quantidade"]):
                raise PedidoRecusadoError("Estoque insuficiente para " + produto["nome"])

    notification_service.pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar_pedidos_usuario(usuario_id):
    return pedido_model.listar(get_db(), usuario_id=usuario_id)


def listar_todos_pedidos():
    return pedido_model.listar(get_db())


def atualizar_status_pedido(pedido_id, dados):
    novo_status = validators.validar_status(dados)
    db = get_db()
    if not pedido_model.existe(db, pedido_id):
        raise NotFoundError("Pedido não encontrado")
    pedido_model.atualizar_status(db, pedido_id, novo_status)
    logger.info("Pedido %s alterado para %s", pedido_id, novo_status)

    if novo_status == pedido_model.STATUS_APROVADO:
        notification_service.pedido_aprovado(pedido_id)
    elif novo_status == pedido_model.STATUS_CANCELADO:
        notification_service.pedido_cancelado(pedido_id)
