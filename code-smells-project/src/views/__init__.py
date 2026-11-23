from .admin_routes import admin_bp
from .pedido_routes import pedido_bp
from .produto_routes import produto_bp
from .relatorio_routes import relatorio_bp
from .sistema_routes import sistema_bp
from .usuario_routes import usuario_bp

_BLUEPRINTS = (sistema_bp, produto_bp, usuario_bp, pedido_bp, relatorio_bp, admin_bp)


def register_blueprints(app):
    for blueprint in _BLUEPRINTS:
        app.register_blueprint(blueprint)
