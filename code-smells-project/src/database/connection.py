"""Conexão SQLite por request (flask.g) e controle explícito de transações."""
import sqlite3
from contextlib import contextmanager

from flask import current_app, g


def connect(database_path):
    # isolation_level=None: autocommit por statement; transações multi-etapa usam transaction().
    conn = sqlite3.connect(database_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE_PATH"])
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@contextmanager
def transaction(db):
    """Executa o bloco numa transação: COMMIT no sucesso, ROLLBACK em qualquer erro."""
    db.execute("BEGIN IMMEDIATE")
    try:
        yield db
    except BaseException:
        db.execute("ROLLBACK")
        raise
    db.execute("COMMIT")


def init_app(app):
    from src.database.schema import init_schema
    from src.database.seed import migrate_plaintext_passwords, seed_if_empty

    app.teardown_appcontext(close_db)
    with app.app_context():
        db = get_db()
        init_schema(db)
        seed_if_empty(db)
        migrate_plaintext_passwords(db)
