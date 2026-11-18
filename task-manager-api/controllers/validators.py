"""Validação centralizada de entrada, com as mesmas mensagens e status que a API já devolvia."""
import re
from datetime import datetime

from config.settings import Settings
from middlewares.error_handler import ValidationError
from models.task import (
    DUE_DATE_FORMAT,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    STATUSES,
)
from models.user import ROLES

EMAIL_PATTERN = re.compile(r'^[A-Za-z0-9+_.-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$')
COLOR_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$')

INVALID_PAYLOAD_MESSAGE = 'Dados inválidos'
PRIORITY_RANGE_MESSAGE = f'Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}'


def require_payload(data, allow_empty=False):
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise ValidationError(INVALID_PAYLOAD_MESSAGE)
    return data


def validate_optional_text(value, error_message):
    if value is not None and not isinstance(value, str):
        raise ValidationError(error_message)
    return value


def parse_optional_int(value, error_message):
    """Converte um parâmetro de query string; vazio significa "sem filtro"."""
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(error_message) from None


# ---- tasks ------------------------------------------------------------------

def validate_title(title):
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def validate_status(status):
    if not isinstance(status, str) or status not in STATUSES:
        raise ValidationError('Status inválido')
    return status


def validate_priority(priority):
    if isinstance(priority, bool) or not isinstance(priority, (int, str)):
        raise ValidationError(PRIORITY_RANGE_MESSAGE)
    try:
        value = int(priority)
    except ValueError:
        raise ValidationError(PRIORITY_RANGE_MESSAGE) from None
    if not MIN_PRIORITY <= value <= MAX_PRIORITY:
        raise ValidationError(PRIORITY_RANGE_MESSAGE)
    return value


def parse_due_date(value, error_message):
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError(error_message) from None


def validate_tags(tags):
    if tags is None or isinstance(tags, str):
        return tags
    if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
        return tags
    raise ValidationError('Tags inválidas')


# ---- users ------------------------------------------------------------------

def validate_name(name):
    if not isinstance(name, str) or not name.strip():
        raise ValidationError('Nome é obrigatório')
    return name


def validate_email(email):
    if not isinstance(email, str) or not EMAIL_PATTERN.match(email):
        raise ValidationError('Email inválido')
    return email


def validate_password(password, too_short_message):
    if not isinstance(password, str) or len(password) < Settings.MIN_PASSWORD_LENGTH:
        raise ValidationError(too_short_message)
    return password


def validate_role(role):
    if not isinstance(role, str) or role not in ROLES:
        raise ValidationError('Role inválido')
    return role


def validate_active(active):
    if not isinstance(active, bool):
        raise ValidationError('Campo active deve ser booleano')
    return active


# ---- categories -------------------------------------------------------------

def validate_color(color):
    if color is not None and (not isinstance(color, str) or not COLOR_PATTERN.match(color)):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')
    return color
