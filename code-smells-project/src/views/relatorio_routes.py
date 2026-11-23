from flask import Blueprint, jsonify

from src.controllers import relatorio_controller
from src.middlewares.auth import require_admin

relatorio_bp = Blueprint("relatorios", __name__)


@relatorio_bp.route("/relatorios/vendas", methods=["GET"])
@require_admin
def relatorio_vendas():
    return jsonify({"dados": relatorio_controller.vendas(), "sucesso": True}), 200
