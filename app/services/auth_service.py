from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models.user import User


def register_user(
    nome,
    email,
    senha,
    ambiente,
    tempo,
    recursos,
    interlocutores
):
    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return None

    senha_hash = generate_password_hash(senha)

    user = User(
        nome=nome,
        email=email,
        senha=senha_hash,
        ambiente=ambiente,
        tempo=tempo,
        recursos=recursos,
        interlocutores=interlocutores
    )

    db.session.add(user)
    db.session.commit()

    return user


def login_user(email, senha):

    user = User.query.filter_by(email=email).first()

    if not user:
        return None

    if not check_password_hash(user.senha, senha):
        return None

    token = create_access_token(
        identity=str(user.id)
    )

    return token