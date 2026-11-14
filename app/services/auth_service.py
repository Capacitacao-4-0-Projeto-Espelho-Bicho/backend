
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models.user import User
from app.models.user_perfil import PerfilUsuario


def register_user(
    nome,
    email,
    senha,
    ambiente,
    tempo,
    recursos,
    interlocutores
):
    email = email.strip().lower()
    existing_user = User.query.filter(func.lower(func.trim(User.email)) == email).first()

    if existing_user:
        return None

    senha_hash = generate_password_hash(senha)

    user = User(
        nome=nome,
        email=email,
        senha_hash=senha_hash
    )

    try:
        db.session.add(user)
        db.session.flush()
        perfil = PerfilUsuario(
            usuario_id=user.id,
            ambiente=ambiente,
            tempo=tempo,
            recursos=recursos,
            interlocutores=interlocutores
        )
        db.session.add(perfil)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        if exc.orig.diag.constraint_name in (
            "uq_usuario_email", "uq_usuario_email_normalizado"
        ):
            return None
        raise

    return user


def login_user(email, senha):
    email = email.strip().lower()
    user = User.query.filter(func.lower(func.trim(User.email)) == email).first()

    if not user or not user.ativo:
        return None

    if not check_password_hash(user.senha_hash, senha):
        return None

    token = create_access_token(identity=str(user.id))
    user.ultimo_login_em = datetime.now(timezone.utc)
    db.session.commit()

    return token
