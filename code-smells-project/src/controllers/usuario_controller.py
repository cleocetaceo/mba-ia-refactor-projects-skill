"""Casos de uso de usuários e autenticação."""
import logging

from src.controllers import validators
from src.database import get_db
from src.middlewares.error_handler import NotFoundError, UnauthorizedError
from src.models import usuario_model
from src.services import password_service

logger = logging.getLogger(__name__)


def _mascarar_email(email):
    usuario, _, dominio = email.partition("@")
    return f"{usuario[:1]}***@{dominio}" if dominio else "***"


def listar():
    return usuario_model.listar(get_db())


def obter(usuario_id):
    usuario = usuario_model.buscar_por_id(get_db(), usuario_id)
    if usuario is None:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar(dados):
    nome, email, senha = validators.validar_usuario(dados)
    db = get_db()
    # O papel nunca vem do cliente: todo cadastro público é "cliente".
    with db:
        usuario_id = usuario_model.criar(db, nome, email, password_service.gerar_hash(senha))
    logger.info("Usuário criado com ID %s", usuario_id)
    return usuario_id


def autenticar(dados):
    email, senha = validators.validar_login(dados)
    for row in usuario_model.buscar_credenciais_por_email(get_db(), email):
        if password_service.verificar(row["senha"], senha):
            logger.info("Login bem-sucedido: %s", _mascarar_email(email))
            return usuario_model.para_login(row)
    logger.warning("Login falhou: %s", _mascarar_email(email))
    raise UnauthorizedError("Email ou senha inválidos", include_sucesso=True)
