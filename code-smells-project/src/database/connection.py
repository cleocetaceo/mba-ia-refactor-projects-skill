"""Conexão SQLite por request (guardada em flask.g), sem estado global compartilhado."""
import sqlite3

from flask import current_app, g


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE_PATH"])
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


def close_db(_exc=None):
    # Fechar sem commit descarta qualquer transação pendente (rollback implícito).
    db = g.pop("db", None)
    if db is not None:
        db.close()
