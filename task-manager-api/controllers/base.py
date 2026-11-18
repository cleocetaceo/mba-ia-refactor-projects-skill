"""Apoio aos controllers: busca por id com 404 e commit transacional."""
import logging

from sqlalchemy.exc import SQLAlchemyError

from database import db
from middlewares.error_handler import AppError, NotFoundError

logger = logging.getLogger(__name__)


def get_or_404(model, identifier, not_found_message):
    if isinstance(identifier, bool) or not isinstance(identifier, (int, str)):
        raise NotFoundError(not_found_message)
    entity = db.session.get(model, identifier)
    if entity is None:
        raise NotFoundError(not_found_message)
    return entity


def commit(error_message):
    """Confirma a unidade de trabalho; em falha desfaz tudo e responde 500 com a mensagem do caso de uso."""
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.exception(error_message)
        raise AppError(error_message, 500) from exc
