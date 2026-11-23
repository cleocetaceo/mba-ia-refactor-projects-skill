"""Autenticação de administrador por token (header X-Admin-Token)."""
import hmac
from functools import wraps

from flask import current_app, jsonify, request


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN")
        if not expected:
            return jsonify({"erro": "Endpoint administrativo desabilitado"}), 403
        provided = request.headers.get("X-Admin-Token", "")
        if not hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8")):
            return jsonify({"erro": "Não autorizado"}), 401
        return view(*args, **kwargs)

    return wrapper
