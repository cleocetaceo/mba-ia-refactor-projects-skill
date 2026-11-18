"""Autenticação administrativa via header X-Admin-Token comparado ao ADMIN_TOKEN da configuração."""
import hmac
from functools import wraps

from flask import current_app, jsonify, request

ADMIN_TOKEN_HEADER = 'X-Admin-Token'


def has_admin_credential():
    expected = current_app.config.get('ADMIN_TOKEN')
    if not expected:
        return False
    provided = request.headers.get(ADMIN_TOKEN_HEADER, '')
    return hmac.compare_digest(provided.encode(), expected.encode())


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_app.config.get('ADMIN_TOKEN'):
            return jsonify({'error': 'Endpoint administrativo desabilitado'}), 403
        if not has_admin_credential():
            return jsonify({'error': 'Não autorizado'}), 401
        return view(*args, **kwargs)

    return wrapper
