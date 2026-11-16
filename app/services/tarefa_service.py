"""Cadastro editorial das questões usadas no nivelamento."""
from app.extensions import db
from app.models import Alternativa, Habilidade, Nivel, Tarefa
from app.services.atividade_service import (
    DadosInvalidos, inteiro, lista, ordens_unicas, pontos, texto,
)


def criar_tarefa(dados):
    try:
        if not isinstance(dados, dict):
            raise DadosInvalidos('Envie um objeto JSON válido.')
        habilidade_id = inteiro(dados.get('habilidade_id'), 'habilidade_id')
        nivel_id = inteiro(dados.get('nivel_id'), 'nivel_id')
        if db.session.get(Habilidade, habilidade_id) is None:
            raise DadosInvalidos('Habilidade não encontrada.')
        if db.session.get(Nivel, nivel_id) is None:
            raise DadosInvalidos('Nível não encontrado.')
        alternativas = lista(dados.get('alternativas'), 'alternativas', minimo=2)
        if len(alternativas) > 5:
            raise DadosInvalidos('Cada questão deve conter de duas a cinco alternativas.')
        ordens_unicas(alternativas, 'alternativas')
        tarefa = Tarefa(
            habilidade_id=habilidade_id, nivel_id=nivel_id,
            enunciado=texto(dados, 'enunciado'),
            instrucoes=texto(dados, 'instrucoes', obrigatorio=False),
            ordem=inteiro(dados.get('ordem'), 'ordem'),
            tempo_estimado_min=inteiro(dados.get('tempo_estimado_min', 15), 'tempo_estimado_min'),
        )
        for alternativa in alternativas:
            if alternativa['ordem'] > 5:
                raise DadosInvalidos('A ordem das alternativas deve estar entre 1 e 5.')
            tarefa.alternativas.append(Alternativa(
                texto=texto(alternativa, 'texto'), ordem=alternativa['ordem'],
                pontuacao=pontos(alternativa.get('pontuacao')),
                justificativa=texto(alternativa, 'justificativa', obrigatorio=False),
            ))
        db.session.add(tarefa)
        db.session.commit()
        return tarefa
    except Exception:
        db.session.rollback()
        raise


def serializar_tarefa(tarefa):
    # Resposta editorial: esta operação é exclusiva de gestor/admin.
    dados = {campo: getattr(tarefa, campo) for campo in (
        'id', 'habilidade_id', 'nivel_id', 'enunciado', 'instrucoes', 'ordem', 'tempo_estimado_min',
    )}
    dados['alternativas'] = [
        {
            'id': alternativa.id, 'texto': alternativa.texto, 'ordem': alternativa.ordem,
            'pontuacao': float(alternativa.pontuacao), 'justificativa': alternativa.justificativa,
        }
        for alternativa in sorted(tarefa.alternativas, key=lambda a: a.ordem)
    ]
    return dados
