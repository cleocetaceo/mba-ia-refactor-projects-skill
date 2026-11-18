"""Casos de uso de usuários e autenticação."""
import logging

from src.controllers import validators
from src.database import get_db
from src.middlewares.error_handler import ConflictError, NotFoundError, UnauthorizedError
from src.models import usuario_model
from src.services import password_service

logger = logging.getLogger(__name__)


def listar_usuarios():
    return usuario_model.listar(get_db())


def buscar_usuario(usuario_id):
    usuario = usuario_model.buscar_por_id(get_db(), usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar_usuario(dados):
    novo = validators.validar_novo_usuario(dados)
    db = get_db()
    if usuario_model.email_cadastrado(db, novo["email"]):
        raise ConflictError("Email já cadastrado")
    # O tipo nunca vem do cliente: todo cadastro público é "cliente".
    usuario_id = usuario_model.criar(
        db, novo["nome"], novo["email"], password_service.hash_password(novo["senha"])
    )
    logger.info("Usuário criado com ID %s", usuario_id)
    return {"id": usuario_id}


def login(dados):
    email, senha = validators.validar_login(dados)
    for usuario, senha_hash in usuario_model.buscar_credenciais(get_db(), email):
        if password_service.verify_password(senha_hash, senha):
            logger.info("Login bem-sucedido para usuário ID %s", usuario["id"])
            return usuario
    logger.warning("Tentativa de login falhou")
    raise UnauthorizedError("Email ou senha inválidos", extra={"sucesso": False})
