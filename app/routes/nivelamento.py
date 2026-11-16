from flask import Blueprint, g, jsonify, request
from flasgger import swag_from
from sqlalchemy.exc import IntegrityError

from app.services.autorizacao import exigir_papeis
from app.services.nivelamento_service import (
    DadosInvalidos, CompetenciaNaoSelecionada, NivelamentoIndisponivel,
    listar_escolhidas, salvar_escolhidas, iniciar_nivelamento,
)

nivelamento_bp = Blueprint('nivelamento', __name__)


@nivelamento_bp.put('/usuarios/me/competencias')
@exigir_papeis('usuario', 'gestor', 'admin')
@swag_from('../docs/salvar_competencias.yml')
def selecionar_competencias():
    try:
        resultado = salvar_escolhidas(g.usuario_atual.id, request.get_json(silent=True))
    except DadosInvalidos as exc:
        return jsonify(error=str(exc)), 400
    except IntegrityError:
        return jsonify(error='Conflito ao salvar a seleção. Nenhuma alteração foi aplicada.'), 409
    return jsonify(resultado), 200


@nivelamento_bp.get('/usuarios/me/competencias')
@exigir_papeis('usuario', 'gestor', 'admin')
@swag_from('../docs/competencias_escolhidas.yml')
def competencias_escolhidas():
    return jsonify(listar_escolhidas(g.usuario_atual.id)), 200


@nivelamento_bp.post('/usuarios/me/competencias/<int:competencia_id>/nivelamento')
@exigir_papeis('usuario', 'gestor', 'admin')
@swag_from('../docs/iniciar_nivelamento.yml')
def obter_nivelamento(competencia_id):
    try:
        resultado, status = iniciar_nivelamento(g.usuario_atual.id, competencia_id)
    except CompetenciaNaoSelecionada as exc:
        return jsonify(error=str(exc)), 404
    except NivelamentoIndisponivel as exc:
        return jsonify(error=str(exc)), 409
    except IntegrityError:
        return jsonify(error='Conflito ao iniciar o nivelamento. Nenhuma avaliação parcial foi criada.'), 409
    return jsonify(resultado), status
