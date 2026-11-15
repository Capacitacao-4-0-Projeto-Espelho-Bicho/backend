from functools import wraps

from flask import g, jsonify
from flask_jwt_extended import get_jwt_identity

from app.extensions import db
from app.models import User


def exigir_papeis(*papeis):
    """Consulta o papel atual no banco; alterações valem para tokens já emitidos."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            identidade = get_jwt_identity()
            try:
                usuario_id = int(identidade)
                if not 0 < usuario_id <= 2147483647:
                    raise ValueError
            except (TypeError, ValueError):
                return jsonify(error='Usuário inválido.'), 401
            usuario = db.session.get(User, usuario_id)
            if usuario is None or not usuario.ativo:
                return jsonify(error='Usuário inexistente ou inativo.'), 401
            if usuario.papel not in papeis:
                return jsonify(error='Você não tem permissão para esta ação.'), 403
            g.usuario_atual = usuario
            return func(*args, **kwargs)
        return wrapper
    return decorator
