"""Composition root: cria a app, carrega config, inicializa banco, middlewares e rotas."""
import logging

from flask import Flask
from flask_cors import CORS

from src import database
from src.config.settings import Settings
from src.middlewares.error_handler import register_error_handlers
from src.views import register_blueprints

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(Settings)
    if overrides:
        app.config.update(overrides)

    logging.basicConfig(level=app.config["LOG_LEVEL"], format=LOG_FORMAT)
    CORS(app, origins=app.config["CORS_ORIGINS"])

    register_error_handlers(app)
    register_blueprints(app)
    database.init_app(app)
    return app
