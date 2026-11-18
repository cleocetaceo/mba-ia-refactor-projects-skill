"""Emissão de tokens de sessão assinados com a SECRET_KEY (itsdangerous já vem com o Flask)."""
from flask import current_app
from itsdangerous import URLSafeTimedSerializer

TOKEN_SALT = 'auth-token'


def issue_token(user_id):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=TOKEN_SALT)
    return serializer.dumps({'user_id': user_id})
