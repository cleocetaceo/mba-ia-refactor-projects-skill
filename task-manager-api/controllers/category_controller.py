import logging

from controllers.base import commit, get_or_404
from controllers.validators import require_payload, validate_color, validate_name, validate_optional_text
from database import db
from middlewares.error_handler import ValidationError
from models.category import DEFAULT_COLOR, Category
from models.task import Task

logger = logging.getLogger(__name__)

CATEGORY_NOT_FOUND = 'Categoria não encontrada'
INVALID_DESCRIPTION = 'Descrição inválida'


def list_categories():
    task_counts = Task.count_by_category()
    return [
        {**category.to_dict(), 'task_count': task_counts.get(category.id, 0)}
        for category in Category.list_all()
    ]


def create_category(data):
    data = require_payload(data)

    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')
    category = Category(
        name=validate_name(name),
        description=validate_optional_text(data.get('description', ''), INVALID_DESCRIPTION),
        color=validate_color(data.get('color', DEFAULT_COLOR)),
    )

    db.session.add(category)
    commit('Erro ao criar categoria')
    logger.info('Categoria criada: id=%s', category.id)
    return category.to_dict()


def update_category(category_id, data):
    category = get_or_404(Category, category_id, CATEGORY_NOT_FOUND)
    data = require_payload(data, allow_empty=True)

    changes = {}
    if 'name' in data:
        changes['name'] = validate_name(data['name'])
    if 'description' in data:
        changes['description'] = validate_optional_text(data['description'], INVALID_DESCRIPTION)
    if 'color' in data:
        changes['color'] = validate_color(data['color'])
    for field, value in changes.items():
        setattr(category, field, value)

    commit('Erro ao atualizar')
    logger.info('Categoria atualizada: id=%s', category_id)
    return category.to_dict()


def delete_category(category_id):
    category = get_or_404(Category, category_id, CATEGORY_NOT_FOUND)
    # As tasks da categoria têm category_id anulado pelo relacionamento (mesmo comportamento anterior).
    db.session.delete(category)
    commit('Erro ao deletar')
    logger.info('Categoria deletada: id=%s', category_id)
    return {'message': 'Categoria deletada'}
