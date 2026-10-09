# Aqui é criado o app flask
from flask import Flask

from .config import Config
from .extensions import db, jwt
from flasgger import Swagger


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)

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

    Swagger(app, config=swagger_config)

    # from .routes.auth import auth_bp
    from .routes.auth import auth_bp
    # app.register_blueprint(auth_bp, url_prefix="/api/auth")

    app.register_blueprint(
        auth_bp,
        url_prefix="/api/auth"
    )

    return app

# def create_app():
#     app = Flask(__name__)

#     @app.get("/")
#     def home():
#         return {
#             "message": "Backend funcionando!"
#         }

#     return app