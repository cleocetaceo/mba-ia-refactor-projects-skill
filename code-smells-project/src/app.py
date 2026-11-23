"""Composition root: cria a app, carrega config, inicializa o banco e registra camadas."""
import logging

from flask import Flask
from flask_cors import CORS

from src import database
from src.config import Settings
from src.middlewares.error_handler import register_error_handlers
from src.views import register_blueprints


def _configurar_logging(level):
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")


def _origens_cors(valor):
    if valor.strip() == "*":
        return "*"
    return [origem.strip() for origem in valor.split(",") if origem.strip()]


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(Settings)
    if overrides:
        app.config.update(overrides)

    _configurar_logging(app.config["LOG_LEVEL"])
    CORS(app, origins=_origens_cors(app.config["CORS_ORIGINS"]))

    database.init_app(app)
    register_error_handlers(app)
    register_blueprints(app)
    return app
