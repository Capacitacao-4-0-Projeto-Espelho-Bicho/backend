from flask import Blueprint, jsonify, request

from app.services.auth_service import (
    register_user,
    login_user
)


auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():

    data = request.get_json()

    required_fields = [
        "nome",
        "email",
        "senha",
        "ambiente",
        "tempo",
        "recursos",
        "interlocutores"
    ]

    for field in required_fields:
        if not data.get(field):
            return jsonify({
                "error": f"O campo '{field}' é obrigatório."
            }), 400

    user = register_user(
        nome=data["nome"],
        email=data["email"],
        senha=data["senha"],
        ambiente=data["ambiente"],
        tempo=data["tempo"],
        recursos=data["recursos"],
        interlocutores=data["interlocutores"]
    )

    if user is None:
        return jsonify({
            "error": "Email já cadastrado."
        }), 409

    return jsonify({
        "message": "Usuário cadastrado com sucesso.",
        "user": {
            "id": user.id,
            "nome": user.nome,
            "email": user.email
        }
    }), 201


@auth_bp.post("/login")
def login():

    data = request.get_json()

    email = data.get("email")
    senha = data.get("senha")

    if not email or not senha:
        return jsonify({
            "error": "Email e senha são obrigatórios."
        }), 400

    token = login_user(email, senha)

    if token is None:
        return jsonify({
            "error": "Email ou senha inválidos."
        }), 401

    return jsonify({
        "access_token": token
    }), 200