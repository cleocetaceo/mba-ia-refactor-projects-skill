import hashlib
import hmac
import re

from sqlalchemy import func, select
from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.helpers import utcnow

ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'

# Formato dos hashes MD5 sem salt gravados pela versão anterior (aceito só para migração).
_LEGACY_MD5_HASH = re.compile(r'^[0-9a-f]{32}$')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        """Serialização pública (allowlist): a senha/hash nunca sai da API."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    # ---- senha --------------------------------------------------------------

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        if self.has_legacy_password_hash():
            legacy_hash = hashlib.md5(raw_password.encode()).hexdigest()
            return hmac.compare_digest(legacy_hash, self.password)
        return check_password_hash(self.password, raw_password)

    def has_legacy_password_hash(self):
        return bool(self.password and _LEGACY_MD5_HASH.match(self.password))

    # ---- consultas ----------------------------------------------------------

    @classmethod
    def list_all(cls):
        return db.session.scalars(select(cls).order_by(cls.id)).all()

    @classmethod
    def find_by_email(cls, email):
        return db.session.scalars(select(cls).where(cls.email == email)).first()

    @classmethod
    def count_all(cls):
        return db.session.scalar(select(func.count(cls.id)))
