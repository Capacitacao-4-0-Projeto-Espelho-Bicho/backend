
from flask import Blueprint, jsonify, request

from app.services.auth_service import (
    register_user,
    login_user
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    """
    Cadastra um novo usuário.
    ---
    tags:
      - Autenticação
    summary: Registrar usuário
    description: >
      Cria uma conta de usuário utilizando os dados do perfil inicial.
      Todos os campos informados abaixo são obrigatórios.
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        description: Dados necessários para cadastrar o usuário.
        schema:
          type: object
          required:
            - nome
            - email
            - senha
            - ambiente
            - tempo
            - recursos
            - interlocutores
          properties:
            nome:
              type: string
              description: Nome do usuário.
              example: Pedro
            email:
              type: string
              format: email
              description: Email utilizado para identificação.
              example: pedro@email.com
            senha:
              type: string
              format: password
              description: Senha da conta.
              example: senha-exemplo
            ambiente:
              type: string
              description: Ambiente predominante de trabalho ou estudo.
              example: individual
            tempo:
              type: string
              description: Tempo disponível para as atividades.
              example: ate_15_min
            recursos:
              type: string
              description: Recursos disponíveis para realizar as atividades.
              example: computador
            interlocutores:
              type: string
              description: Interlocutores presentes durante as atividades.
              example: sozinho
    responses:
      201:
        description: Usuário cadastrado com sucesso.
        schema:
          type: object
          properties:
            message:
              type: string
              example: Usuário cadastrado com sucesso.
            user:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                nome:
                  type: string
                  example: Pedro
                email:
                  type: string
                  example: pedro@email.com
      400:
        description: Campo obrigatório ausente ou vazio.
        schema:
          type: object
          properties:
            error:
              type: string
              example: O campo 'nome' é obrigatório.
      409:
        description: Email já cadastrado.
        schema:
          type: object
          properties:
            error:
              type: string
              example: Email já cadastrado.
    """
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
    """
    Autentica um usuário.
    ---
    tags:
      - Autenticação
    summary: Realizar login
    description: >
      Valida as credenciais do usuário e retorna um token de acesso JWT
      quando a autenticação é bem-sucedida.
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        description: Credenciais do usuário.
        schema:
          type: object
          required:
            - email
            - senha
          properties:
            email:
              type: string
              format: email
              description: Email cadastrado.
              example: pedro@email.com
            senha:
              type: string
              format: password
              description: Senha da conta.
              example: senha-exemplo
    responses:
      200:
        description: Autenticação realizada com sucesso.
        schema:
          type: object
          properties:
            access_token:
              type: string
              description: Token JWT para autenticação nas rotas protegidas.
              example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
      400:
        description: Email ou senha não informados.
        schema:
          type: object
          properties:
            error:
              type: string
              example: Email e senha são obrigatórios.
      401:
        description: Credenciais inválidas.
        schema:
          type: object
          properties:
            error:
              type: string
              example: Email ou senha inválidos.
    """
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
