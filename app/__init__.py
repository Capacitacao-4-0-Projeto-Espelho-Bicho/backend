# Aqui é criado o app flask
from flask import Flask, request
from flask_jwt_extended import verify_jwt_in_request

from .config import Config
from .extensions import db, jwt
from flasgger import Swagger


def create_app(config=None):
    app = Flask(__name__)

    app.config.from_object(Config)
    if config:
        app.config.update(config)

    db.init_app(app)
    jwt.init_app(app)

    # Rotas públicas que não exigem autenticação (login é onde o usuário recebe 
    # o token JWT pela primeira vez)
    rotas_publicas = frozenset({"auth.login", "auth.register"})

    @app.before_request
    def exigir_autenticacao():
        # Novas rotas da API exigem JWT sem depender de decoradores individuais.
        if request.method == "OPTIONS":
            return
        if request.path != "/api" and not request.path.startswith("/api/"):
            return
        if request.endpoint in rotas_publicas:
            return
        verify_jwt_in_request()

    # Registra os modelos no SQLAlchemy
    from app import models

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apispec_1.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/dev",
    }

    swagger_template = {
        "swagger": "2.0",
        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Informe Bearer seguido de um espaço e do token retornado pelo login.",
            }
        },
    }
    Swagger(app, config=swagger_config, template=swagger_template)

    from .routes.auth import auth_bp
    from .routes.catalogo import catalogo_bp

    app.register_blueprint(
        auth_bp,
        url_prefix="/api/auth"
    )

    app.register_blueprint(catalogo_bp, url_prefix="/api")

    return app


# def create_app():
#     app = Flask(__name__)

#     @app.get("/")
#     def home():
#         return {
#             "message": "Backend funcionando!"
#         }

#     return app