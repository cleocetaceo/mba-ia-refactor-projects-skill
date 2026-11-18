"""Erros de domínio e tratamento central de erros (formato {"error": "..."} usado pela API)."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

GENERIC_ERROR_MESSAGE = 'Erro interno'


class AppError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': err.message}), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify({'error': err.description}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(_err):
        logger.exception('Erro inesperado ao processar a requisição')
        return jsonify({'error': GENERIC_ERROR_MESSAGE}), 500
