"""Erros de domínio e tratamento central de exceções (formato {"erro": ...} da API)."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, extra=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        # Chaves adicionais do corpo de erro (ex.: {"sucesso": False}), preservando o formato original.
        self.extra = extra or {}


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class HealthCheckError(AppError):
    status_code = 500


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message, **err.extra}), err.status_code

    @app.errorhandler(HealthCheckError)
    def handle_health_error(err):
        return jsonify({"status": "erro", "detalhes": err.message}), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify({"erro": err.description}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(_err):
        logger.exception("Erro inesperado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
