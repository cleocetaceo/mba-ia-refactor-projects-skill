import logging

from controllers.base import commit, get_or_404
from controllers.validators import (
    parse_due_date,
    parse_optional_int,
    require_payload,
    validate_optional_text,
    validate_priority,
    validate_status,
    validate_tags,
    validate_title,
)
from database import db
from middlewares.error_handler import ValidationError
from models.category import Category
from models.task import DEFAULT_PRIORITY, DEFAULT_STATUS, DONE_STATUS, STATUSES, Task
from models.user import User
from utils.helpers import calculate_percentage, utcnow

logger = logging.getLogger(__name__)

TASK_NOT_FOUND = 'Task não encontrada'
USER_NOT_FOUND = 'Usuário não encontrado'
CATEGORY_NOT_FOUND = 'Categoria não encontrada'
INVALID_DESCRIPTION = 'Descrição inválida'


def list_tasks():
    tasks = Task.list_all(with_relations=True)
    return [task.to_dict(include_overdue=True, include_relations=True) for task in tasks]


def get_task(task_id):
    return get_or_404(Task, task_id, TASK_NOT_FOUND).to_dict(include_overdue=True)


def create_task(data):
    data = require_payload(data)

    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')
    validate_title(title)
    description = validate_optional_text(data.get('description', ''), INVALID_DESCRIPTION)
    status = validate_status(data.get('status', DEFAULT_STATUS))
    priority = validate_priority(data.get('priority', DEFAULT_PRIORITY))

    user_id = data.get('user_id')
    if user_id:
        get_or_404(User, user_id, USER_NOT_FOUND)
    category_id = data.get('category_id')
    if category_id:
        get_or_404(Category, category_id, CATEGORY_NOT_FOUND)

    task = Task(title=title, description=description, status=status, priority=priority,
                user_id=user_id, category_id=category_id)
    if data.get('due_date'):
        task.due_date = parse_due_date(data['due_date'], 'Formato de data inválido. Use YYYY-MM-DD')
    if data.get('tags'):
        task.set_tags(validate_tags(data['tags']))

    db.session.add(task)
    commit('Erro ao criar task')
    logger.info('Task criada: id=%s', task.id)
    return task.to_dict()


def update_task(task_id, data):
    task = get_or_404(Task, task_id, TASK_NOT_FOUND)
    data = require_payload(data)

    # Valida tudo antes de alterar a entidade.
    changes = {}
    if 'title' in data:
        changes['title'] = validate_title(data['title'])
    if 'description' in data:
        changes['description'] = validate_optional_text(data['description'], INVALID_DESCRIPTION)
    if 'status' in data:
        changes['status'] = validate_status(data['status'])
    if 'priority' in data:
        changes['priority'] = validate_priority(data['priority'])
    if 'user_id' in data:
        if data['user_id']:
            get_or_404(User, data['user_id'], USER_NOT_FOUND)
        changes['user_id'] = data['user_id']
    if 'category_id' in data:
        if data['category_id']:
            get_or_404(Category, data['category_id'], CATEGORY_NOT_FOUND)
        changes['category_id'] = data['category_id']
    if 'due_date' in data:
        due_date = data['due_date']
        changes['due_date'] = parse_due_date(due_date, 'Formato de data inválido') if due_date else None
    tags = validate_tags(data['tags']) if 'tags' in data else None

    for field, value in changes.items():
        setattr(task, field, value)
    if 'tags' in data:
        task.set_tags(tags)
    task.updated_at = utcnow()

    commit('Erro ao atualizar')
    logger.info('Task atualizada: id=%s', task.id)
    return task.to_dict()


def delete_task(task_id):
    task = get_or_404(Task, task_id, TASK_NOT_FOUND)
    db.session.delete(task)
    commit('Erro ao deletar')
    logger.info('Task deletada: id=%s', task_id)
    return {'message': 'Task deletada com sucesso'}


def search_tasks(text, status, priority, user_id):
    tasks = Task.search(
        text=text or None,
        status=status or None,
        priority=parse_optional_int(priority, 'Parâmetro priority inválido'),
        user_id=parse_optional_int(user_id, 'Parâmetro user_id inválido'),
    )
    return [task.to_dict() for task in tasks]


def task_stats():
    counts = Task.count_by_status()
    total = sum(counts.values())
    done = counts.get(DONE_STATUS, 0)
    stats = {status: counts.get(status, 0) for status in STATUSES}
    stats.update({
        'total': total,
        'overdue': len(Task.list_overdue()),
        'completion_rate': calculate_percentage(done, total),
    })
    return stats
