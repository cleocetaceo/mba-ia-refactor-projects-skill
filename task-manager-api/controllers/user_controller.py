import logging

from config.settings import Settings
from controllers.base import commit, get_or_404
from controllers.validators import (
    require_payload,
    validate_active,
    validate_email,
    validate_name,
    validate_password,
    validate_role,
)
from database import db
from middlewares.error_handler import ConflictError, ForbiddenError, UnauthorizedError, ValidationError
from models.task import Task
from models.user import DEFAULT_ROLE, User
from services.token_service import issue_token

logger = logging.getLogger(__name__)

USER_NOT_FOUND = 'Usuário não encontrado'
EMAIL_TAKEN = 'Email já cadastrado'
INVALID_CREDENTIALS = 'Credenciais inválidas'


def list_users():
    task_counts = Task.count_by_user()
    return [
        {**user.to_dict(), 'task_count': task_counts.get(user.id, (0, 0))[0]}
        for user in User.list_all()
    ]


def get_user(user_id):
    user = get_or_404(User, user_id, USER_NOT_FOUND)
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in Task.list_by_user(user_id)]
    return data


def create_user(data, allow_privileged_role=False):
    data = require_payload(data)

    name, email, password = data.get('name'), data.get('email'), data.get('password')
    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    validate_name(name)
    validate_email(email)
    validate_password(password, f'Senha deve ter no mínimo {Settings.MIN_PASSWORD_LENGTH} caracteres')
    if User.find_by_email(email):
        raise ConflictError(EMAIL_TAKEN)
    role = validate_role(data.get('role', DEFAULT_ROLE))
    if role != DEFAULT_ROLE and not allow_privileged_role:
        logger.warning('Role "%s" ignorado na criação de usuário: requisição sem credencial de admin', role)
        role = DEFAULT_ROLE

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    commit('Erro ao criar usuário')
    logger.info('Usuário criado: id=%s', user.id)
    return user.to_dict()


def update_user(user_id, data, allow_privileged_role=False):
    user = get_or_404(User, user_id, USER_NOT_FOUND)
    data = require_payload(data)

    # Valida tudo antes de alterar a entidade.
    changes = {}
    if 'name' in data:
        changes['name'] = validate_name(data['name'])
    if 'email' in data:
        email = validate_email(data['email'])
        existing = User.find_by_email(email)
        if existing and existing.id != user_id:
            raise ConflictError(EMAIL_TAKEN)
        changes['email'] = email
    new_password = validate_password(data['password'], 'Senha muito curta') if 'password' in data else None
    if 'role' in data:
        role = validate_role(data['role'])
        if allow_privileged_role:
            changes['role'] = role
        else:
            logger.warning('Alteração de role ignorada para o usuário id=%s: requisição sem credencial de admin',
                           user_id)
    if 'active' in data:
        changes['active'] = validate_active(data['active'])

    for field, value in changes.items():
        setattr(user, field, value)
    if new_password is not None:
        user.set_password(new_password)

    commit('Erro ao atualizar')
    logger.info('Usuário atualizado: id=%s', user_id)
    return user.to_dict()


def delete_user(user_id):
    user = get_or_404(User, user_id, USER_NOT_FOUND)
    # Remove as tasks do usuário e o próprio usuário na mesma transação.
    for task in Task.list_by_user(user_id):
        db.session.delete(task)
    db.session.delete(user)
    commit('Erro ao deletar')
    logger.info('Usuário deletado: id=%s', user_id)
    return {'message': 'Usuário deletado com sucesso'}


def list_user_tasks(user_id):
    get_or_404(User, user_id, USER_NOT_FOUND)
    return [task.to_summary_dict() for task in Task.list_by_user(user_id)]


def login(data):
    data = require_payload(data)

    email, password = data.get('email'), data.get('password')
    if not email or not password or not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError('Email e senha são obrigatórios')

    user = User.find_by_email(email)
    if not user or not user.check_password(password):
        raise UnauthorizedError(INVALID_CREDENTIALS)
    if not user.active:
        raise ForbiddenError('Usuário inativo')

    if user.has_legacy_password_hash():
        # Migração transparente: hash MD5 legado é regravado com hash forte após login válido.
        user.set_password(password)
        commit('Erro ao atualizar senha')
        logger.info('Hash de senha migrado para o usuário id=%s', user.id)

    logger.info('Login realizado: user_id=%s', user.id)
    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': issue_token(user.id),
    }
