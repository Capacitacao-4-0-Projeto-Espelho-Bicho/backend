from flask import Blueprint, jsonify, request
from flasgger import swag_from
from sqlalchemy.exc import IntegrityError

from app.services.autorizacao import exigir_papeis
from app.services.tarefa_service import DadosInvalidos, criar_tarefa, serializar_tarefa


tarefas_bp = Blueprint('tarefas', __name__)


@tarefas_bp.post('/tarefas')
@exigir_papeis('gestor', 'admin')
@swag_from('../docs/criar_tarefa.yml')
def cadastrar_tarefa():
    try:
        tarefa = criar_tarefa(request.get_json(silent=True))
    except DadosInvalidos as exc:
        return jsonify(error=str(exc)), 400
    except IntegrityError:
        return jsonify(error='Os dados conflitam com os cadastros existentes. Nenhuma questão foi criada.'), 409
    return jsonify(serializar_tarefa(tarefa)), 201
