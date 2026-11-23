from flask import Blueprint, jsonify, request

from src.controllers import admin_controller
from src.middlewares.auth import require_admin

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/reset-db", methods=["POST"])
@require_admin
def reset_database():
    admin_controller.resetar_banco()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


@admin_bp.route("/admin/query", methods=["POST"])
@require_admin
def executar_query():
    resultado = admin_controller.executar_query(request.get_json(silent=True))
    return jsonify({"dados": resultado, "sucesso": True}), 200
