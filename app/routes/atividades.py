from flask import Blueprint, g, jsonify, request
from flasgger import swag_from
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Atividade, AtividadeQuestao
from app.services.autorizacao import exigir_papeis
from app.services.atividade_service import (
    DadosInvalidos, criar_atividade, inteiro, serializar_atividade,
)

atividades_bp = Blueprint('atividades', __name__)


@atividades_bp.post('/atividades')
@exigir_papeis('gestor', 'admin')
@swag_from('../docs/criar_atividade.yml')
def cadastrar_atividade():
    try:
        atividade = criar_atividade(request.get_json(silent=True))
    except DadosInvalidos as exc:
        return jsonify(error=str(exc)), 400
    except IntegrityError:
        return jsonify(error='Os dados conflitam com os cadastros existentes. Nenhuma atividade foi criada.'), 409
    return jsonify(serializar_atividade(atividade, detalhe=True, editorial=True)), 201


@atividades_bp.get('/atividades')
@exigir_papeis('usuario', 'gestor', 'admin')
@swag_from('../docs/listar_atividades.yml')
def listar_atividades():
    consulta = db.select(Atividade).order_by(Atividade.id)
    try:
        for campo in ('competencia_id', 'habilidade_id', 'dificuldade'):
            if campo in request.args:
                try:
                    valor = int(request.args[campo])
                except ValueError:
                    raise DadosInvalidos(f'{campo} deve ser um inteiro positivo.')
                consulta = consulta.where(getattr(Atividade, campo) == inteiro(valor, campo))
    except DadosInvalidos as exc:
        return jsonify(error=str(exc)), 400
    return jsonify([serializar_atividade(a) for a in db.session.scalars(consulta).all()]), 200


@atividades_bp.get('/atividades/<int:atividade_id>')
@exigir_papeis('usuario', 'gestor', 'admin')
@swag_from('../docs/detalhar_atividade.yml')
def detalhar_atividade(atividade_id):
    atividade = db.session.scalar(
        db.select(Atividade).where(Atividade.id == atividade_id).options(
            selectinload(Atividade.questoes).selectinload(AtividadeQuestao.alternativas)
        )
    )
    if atividade is None:
        return jsonify(error='Atividade não encontrada.'), 404
    return jsonify(serializar_atividade(
        atividade, detalhe=True, editorial=g.usuario_atual.papel in ('admin', 'gestor')
    )), 200
