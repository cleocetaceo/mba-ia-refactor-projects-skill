"""Entry point e composition root da Task Manager API."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes import register_blueprints


def create_app(settings=Settings):
    app = Flask(__name__)
    app.config.from_object(settings)

    logging.basicConfig(
        level=app.config['LOG_LEVEL'],
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    )

    CORS(app, origins=app.config['CORS_ORIGINS'])
    db.init_app(app)
    register_error_handlers(app)
    register_blueprints(app)  # importa controllers e models, registrando as tabelas no metadata

    with app.app_context():
        db.create_all()

    return app


# Mantido no nível do módulo: seed.py faz `from app import app, db`.
app = create_app()

if __name__ == '__main__':
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
