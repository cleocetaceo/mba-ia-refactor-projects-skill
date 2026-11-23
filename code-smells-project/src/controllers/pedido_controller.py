"""Casos de uso de pedidos."""
import logging

from src.controllers import validators
from src.database import get_db
from src.middlewares.error_handler import NotFoundError, ValidationError
from src.models import pedido_model, produto_model
from src.services import notification_service

logger = logging.getLogger(__name__)


def _estoque_insuficiente(produto):
    return ValidationError("Estoque insuficiente para " + produto["nome"], include_sucesso=True)


def criar(dados):
    usuario_id, itens = validators.validar_pedido(dados)
    db = get_db()
    try:
        # Trava de escrita desde a leitura do estoque até o commit: pedido, itens e baixa são atômicos.
        db.execute("BEGIN IMMEDIATE")
        produtos = produto_model.buscar_por_ids(db, [item["produto_id"] for item in itens])

        total = 0
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise ValidationError(f"Produto {item['produto_id']} não encontrado", include_sucesso=True)
            if produto["estoque"] < item["quantidade"]:
                raise _estoque_insuficiente(produto)
            total = total + (produto["preco"] * item["quantidade"])

        pedido_id = pedido_model.inserir(db, usuario_id, total)
        for item in itens:
            produto = produtos[item["produto_id"]]
            pedido_model.inserir_item(db, pedido_id, item["produto_id"], item["quantidade"], produto["preco"])
            # Baixa condicional protege contra itens repetidos e pedidos concorrentes.
            if not produto_model.baixar_estoque(db, item["produto_id"], item["quantidade"]):
                raise _estoque_insuficiente(produto)
        db.commit()
    except Exception:
        db.rollback()
        raise

    logger.info("Pedido %s criado para usuario %s", pedido_id, usuario_id)
    notification_service.pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar_todos():
    return pedido_model.listar(get_db())


def listar_por_usuario(usuario_id):
    return pedido_model.listar(get_db(), usuario_id=usuario_id)


def atualizar_status(pedido_id, dados):
    novo_status = validators.validar_status_pedido(dados)
    db = get_db()
    with db:
        if not pedido_model.atualizar_status(db, pedido_id, novo_status):
            raise NotFoundError("Pedido não encontrado")

    if novo_status == pedido_model.STATUS_APROVADO:
        notification_service.pedido_aprovado(pedido_id)
    elif novo_status == pedido_model.STATUS_CANCELADO:
        notification_service.pedido_cancelado(pedido_id)
