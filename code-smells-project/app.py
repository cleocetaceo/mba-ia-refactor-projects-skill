"""Entry point: python app.py"""
import logging

from src.app import create_app

app = create_app()
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    host, port = app.config["HOST"], app.config["PORT"]
    logger.info("SERVIDOR INICIADO - rodando em http://%s:%s", host, port)
    app.run(host=host, port=port, debug=app.config["DEBUG"])
