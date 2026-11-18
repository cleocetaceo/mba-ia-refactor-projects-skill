from flask import Blueprint, jsonify, request

from src.controllers import usuario_controller

usuario_bp = Blueprint("usuarios", __name__)


@usuario_bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    return jsonify({"dados": usuario_controller.listar_usuarios(), "sucesso": True}), 200


@usuario_bp.route("/usuarios/<int:usuario_id>", methods=["GET"])
def buscar_usuario(usuario_id):
    return jsonify({"dados": usuario_controller.buscar_usuario(usuario_id), "sucesso": True}), 200


@usuario_bp.route("/usuarios", methods=["POST"])
def criar_usuario():
    criado = usuario_controller.criar_usuario(request.get_json(silent=True))
    return jsonify({"dados": criado, "sucesso": True}), 201


@usuario_bp.route("/login", methods=["POST"])
def login():
    usuario = usuario_controller.login(request.get_json(silent=True))
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
