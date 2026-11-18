from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import joinedload

from database import db
from utils.helpers import utcnow

STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
CLOSED_STATUSES = ('done', 'cancelled')
DONE_STATUS = 'done'
DEFAULT_STATUS = 'pending'

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2  # prioridades 1 e 2 contam como "alta prioridade"
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
DUE_DATE_FORMAT = '%Y-%m-%d'
TAG_SEPARATOR = ','


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(MAX_TITLE_LENGTH), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    # ---- regras da entidade -------------------------------------------------

    def is_overdue(self, now=None):
        if not self.due_date or self.status in CLOSED_STATUSES:
            return False
        return self.due_date < (now or utcnow())

    def is_high_priority(self):
        return self.priority is not None and self.priority <= HIGH_PRIORITY_MAX

    def set_tags(self, tags):
        self.tags = TAG_SEPARATOR.join(tags) if isinstance(tags, list) else tags

    # ---- serialização -------------------------------------------------------

    def to_dict(self, include_overdue=False, include_relations=False):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(TAG_SEPARATOR) if self.tags else [],
        }
        if include_overdue:
            data['overdue'] = self.is_overdue()
        if include_relations:
            data['user_name'] = self.user.name if self.user else None
            data['category_name'] = self.category.name if self.category else None
        return data

    def to_summary_dict(self):
        """Formato resumido usado na listagem de tasks de um usuário."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(),
        }

    # ---- consultas ----------------------------------------------------------

    @classmethod
    def list_all(cls, with_relations=False):
        stmt = select(cls).order_by(cls.id)
        if with_relations:
            stmt = stmt.options(joinedload(cls.user), joinedload(cls.category))
        return db.session.scalars(stmt).all()

    @classmethod
    def list_by_user(cls, user_id):
        return db.session.scalars(select(cls).where(cls.user_id == user_id).order_by(cls.id)).all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        stmt = select(cls)
        if text:
            pattern = f'%{text}%'
            stmt = stmt.where(or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            stmt = stmt.where(cls.status == status)
        if priority is not None:
            stmt = stmt.where(cls.priority == priority)
        if user_id is not None:
            stmt = stmt.where(cls.user_id == user_id)
        return db.session.scalars(stmt.order_by(cls.id)).all()

    @classmethod
    def list_overdue(cls, now=None):
        now = now or utcnow()
        stmt = select(cls).where(cls.due_date.is_not(None), cls.due_date < now).order_by(cls.id)
        return [task for task in db.session.scalars(stmt) if task.is_overdue(now)]

    @classmethod
    def count_by_status(cls):
        rows = db.session.execute(select(cls.status, func.count(cls.id)).group_by(cls.status)).all()
        return {status: count for status, count in rows}

    @classmethod
    def count_by_priority(cls):
        rows = db.session.execute(select(cls.priority, func.count(cls.id)).group_by(cls.priority)).all()
        return {priority: count for priority, count in rows}

    @classmethod
    def count_by_category(cls):
        rows = db.session.execute(select(cls.category_id, func.count(cls.id)).group_by(cls.category_id)).all()
        return {category_id: count for category_id, count in rows}

    @classmethod
    def count_by_user(cls):
        """Retorna {user_id: (total_de_tasks, tasks_concluidas)} numa única query."""
        done = func.sum(case((cls.status == DONE_STATUS, 1), else_=0))
        rows = db.session.execute(select(cls.user_id, func.count(cls.id), done).group_by(cls.user_id)).all()
        return {user_id: (total, completed or 0) for user_id, total, completed in rows}

    @classmethod
    def count_created_since(cls, since):
        return db.session.scalar(select(func.count(cls.id)).where(cls.created_at >= since))

    @classmethod
    def count_completed_since(cls, since):
        return db.session.scalar(
            select(func.count(cls.id)).where(cls.status == DONE_STATUS, cls.updated_at >= since)
        )
