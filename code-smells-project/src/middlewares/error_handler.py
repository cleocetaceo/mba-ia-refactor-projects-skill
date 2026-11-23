"""Erros de domínio e handler central.

O corpo de erro mantém o formato que a API já usava: {"erro": "..."} e,
nos casos em que o original também enviava, "sucesso": false.
"""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, include_sucesso=False, body=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.include_sucesso = include_sucesso
        self.body = body

    def to_dict(self):
        if self.body is not None:
            return self.body
        payload = {"erro": self.message}
        if self.include_sucesso:
            payload["sucesso"] = False
        return payload


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class NotFoundError(AppError):
    status_code = 404


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify(err.to_dict()), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        # 404/405 de rota inexistente etc. seguem a resposta padrão do Flask, como antes.
        return err

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro inesperado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
