from .connection import close_db, get_db
from .schema import create_schema
from .seed import migrar_senhas_legadas, seed_if_empty


def init_app(app):
    """Registra o fechamento da conexão por request e prepara schema + seed no boot."""
    app.teardown_appcontext(close_db)
    with app.app_context():
        db = get_db()
        create_schema(db)
        seed_if_empty(db)
        migrar_senhas_legadas(db)


__all__ = ["get_db", "close_db", "init_app"]
