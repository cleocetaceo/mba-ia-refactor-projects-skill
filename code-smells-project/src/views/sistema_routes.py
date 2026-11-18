from flask import Blueprint, jsonify

from src.controllers import sistema_controller

sistema_bp = Blueprint("sistema", __name__)


@sistema_bp.route("/", methods=["GET"])
def index():
    return jsonify(sistema_controller.info_api()), 200


@sistema_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify(sistema_controller.health_check()), 200
