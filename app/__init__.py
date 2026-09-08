# Aqui é criado o app flask
from flask import Flask

from .config import Config
from .extensions import db, jwt


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)

    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    return app

# def create_app():
#     app = Flask(__name__)

#     @app.get("/")
#     def home():
#         return {
#             "message": "Backend funcionando!"
#         }

#     return app