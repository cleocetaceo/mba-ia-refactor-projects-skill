from flask import Blueprint, current_app, jsonify

from src.controllers import sistema_controller

sistema_bp = Blueprint("sistema", __name__)


@sistema_bp.route("/", methods=["GET"])
def index():
    return jsonify(sistema_controller.indice())


@sistema_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify(sistema_controller.health(current_app.config["APP_ENV"])), 200
