"""Views: blueprints por domínio. Apenas roteiam, extraem parâmetros e serializam a resposta."""
from src.views.admin_routes import admin_bp
from src.views.pedido_routes import pedido_bp
from src.views.produto_routes import produto_bp
from src.views.relatorio_routes import relatorio_bp
from src.views.sistema_routes import sistema_bp
from src.views.usuario_routes import usuario_bp

BLUEPRINTS = (produto_bp, usuario_bp, pedido_bp, relatorio_bp, sistema_bp, admin_bp)


def register_blueprints(app):
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
