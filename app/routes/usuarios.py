from flask import Blueprint, jsonify, request
from flasgger import swag_from

from app.extensions import db
from app.models import User
from app.services.autorizacao import exigir_papeis

usuarios_bp = Blueprint('usuarios', __name__)


@usuarios_bp.patch('/usuarios/<int:usuario_id>/papel')
@exigir_papeis('admin')
@swag_from('../docs/alterar_papel.yml')
def alterar_papel(usuario_id):
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or dados.get('papel') not in ('usuario', 'gestor', 'admin'):
        return jsonify(error='Informe papel: usuario, gestor ou admin.'), 400
    usuario = db.session.get(User, usuario_id)
    if usuario is None:
        return jsonify(error='Usuário não encontrado.'), 404
    usuario.papel = dados['papel']
    db.session.commit()
    return jsonify(id=usuario.id, papel=usuario.papel), 200
