from collections import Counter
from datetime import timedelta

from controllers.base import get_or_404
from models.category import Category
from models.task import DONE_STATUS, PRIORITY_LABELS, STATUSES, Task
from models.user import User
from utils.helpers import calculate_percentage, utcnow

RECENT_ACTIVITY_DAYS = 7


def summary_report():
    now = utcnow()
    status_counts = Task.count_by_status()
    priority_counts = Task.count_by_priority()
    tasks_per_user = Task.count_by_user()
    overdue_tasks = Task.list_overdue(now)
    recent_since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

    user_productivity = []
    for user in User.list_all():
        total, completed = tasks_per_user.get(user.id, (0, 0))
        user_productivity.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': sum(status_counts.values()),
            'total_users': User.count_all(),
            'total_categories': Category.count_all(),
        },
        'tasks_by_status': {status: status_counts.get(status, 0) for status in STATUSES},
        'tasks_by_priority': {label: priority_counts.get(priority, 0) for priority, label in PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': [
                {
                    'id': task.id,
                    'title': task.title,
                    'due_date': str(task.due_date),
                    'days_overdue': (now - task.due_date).days,
                }
                for task in overdue_tasks
            ],
        },
        'recent_activity': {
            'tasks_created_last_7_days': Task.count_created_since(recent_since),
            'tasks_completed_last_7_days': Task.count_completed_since(recent_since),
        },
        'user_productivity': user_productivity,
    }


def user_report(user_id):
    user = get_or_404(User, user_id, 'Usuário não encontrado')
    tasks = Task.list_by_user(user_id)
    now = utcnow()
    by_status = Counter(task.status for task in tasks)
    done = by_status[DONE_STATUS]

    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': len(tasks),
            'done': done,
            'pending': by_status['pending'],
            'in_progress': by_status['in_progress'],
            'cancelled': by_status['cancelled'],
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks if task.is_high_priority()),
            'completion_rate': calculate_percentage(done, len(tasks)),
        },
    }
