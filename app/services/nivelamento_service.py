"""Seleção pessoal de competências e início/retomada do nivelamento."""
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import (
    User, Competencia, UsuarioCompetencia, AvaliacaoUsuario, AvaliacaoTarefa,
    Tarefa, Habilidade, Nivel,
)
from app.services.atividade_service import DadosInvalidos, inteiro


class NivelamentoIndisponivel(ValueError):
    pass


class CompetenciaNaoSelecionada(LookupError):
    pass


def bloquear_usuario(usuario_id):
    # Seleção e início usam o mesmo bloqueio para serializar chamadas concorrentes.
    db.session.execute(db.select(User.id).where(User.id == usuario_id).with_for_update()).one()


def listar_escolhidas(usuario_id):
    competencias = db.session.scalars(
        db.select(Competencia).join(UsuarioCompetencia,
            UsuarioCompetencia.competencia_id == Competencia.id).where(
                UsuarioCompetencia.usuario_id == usuario_id, UsuarioCompetencia.ativa.is_(True)
            ).order_by(Competencia.id)
    ).all()
    if not competencias:
        return []
    avaliacoes = db.session.execute(
        db.select(AvaliacaoUsuario, Nivel).outerjoin(Nivel, Nivel.id == AvaliacaoUsuario.nivel_id).where(
            AvaliacaoUsuario.usuario_id == usuario_id,
            AvaliacaoUsuario.tipo == 'nivelamento',
            AvaliacaoUsuario.competencia_id.in_([c.id for c in competencias]),
        ).order_by(AvaliacaoUsuario.id.desc())
    ).all()
    recentes = {}
    for avaliacao, nivel in avaliacoes:
        recentes.setdefault(avaliacao.competencia_id, (avaliacao, nivel))
    resultado = []
    for competencia in competencias:
        avaliacao, nivel = recentes.get(competencia.id, (None, None))
        pendente = avaliacao is None or avaliacao.status == 'cancelada'
        resultado.append({
            'competencia_id': competencia.id, 'nome': competencia.nome,
            'descricao': competencia.descricao,
            'nivelamento': {
                'status': 'pendente' if pendente else avaliacao.status,
                'avaliacao_id': None if pendente else avaliacao.id,
                'nivel': {'id': nivel.id, 'nome': nivel.nome} if nivel and not pendente else None,
            },
        })
    return resultado


def salvar_escolhidas(usuario_id, dados):
    try:
        if not isinstance(dados, dict) or not isinstance(dados.get('competencia_ids'), list):
            raise DadosInvalidos('Envie competencia_ids como uma lista de IDs.')
        ids = [inteiro(valor, 'competencia_ids') for valor in dados['competencia_ids']]
        if len(set(ids)) != len(ids):
            raise DadosInvalidos('competencia_ids não pode conter IDs repetidos.')
        bloquear_usuario(usuario_id)
        encontrados = set(db.session.scalars(db.select(Competencia.id).where(Competencia.id.in_(ids))).all())
        if encontrados != set(ids):
            raise DadosInvalidos('Uma ou mais competências não existem.')
        existentes = db.session.scalars(db.select(UsuarioCompetencia).where(
            UsuarioCompetencia.usuario_id == usuario_id
        )).all()
        for selecao in existentes:
            selecao.ativa = selecao.competencia_id in encontrados
        cadastradas = {s.competencia_id for s in existentes}
        for competencia_id in encontrados - cadastradas:
            db.session.add(UsuarioCompetencia(usuario_id=usuario_id, competencia_id=competencia_id))
        db.session.flush()
        resultado = listar_escolhidas(usuario_id)
        db.session.commit()
        return resultado
    except Exception:
        db.session.rollback()
        raise


def serializar_avaliacao(avaliacao):
    tarefas = db.session.scalars(
        db.select(Tarefa).join(AvaliacaoTarefa, AvaliacaoTarefa.tarefa_id == Tarefa.id)
        .join(Habilidade, Habilidade.id == Tarefa.habilidade_id)
        .where(AvaliacaoTarefa.avaliacao_id == avaliacao.id)
        .options(selectinload(Tarefa.alternativas))
        .order_by(Habilidade.ordem, Habilidade.id, Tarefa.ordem, Tarefa.id)
    ).all()
    return {
        'avaliacao_id': avaliacao.id, 'competencia_id': avaliacao.competencia_id,
        'status': avaliacao.status,
        'questoes': [
            {
                'id': tarefa.id, 'habilidade_id': tarefa.habilidade_id,
                'enunciado': tarefa.enunciado, 'instrucoes': tarefa.instrucoes,
                'ordem': tarefa.ordem, 'tempo_estimado_min': tarefa.tempo_estimado_min,
                'alternativas': [
                    {'id': a.id, 'texto': a.texto, 'ordem': a.ordem}
                    for a in sorted(tarefa.alternativas, key=lambda a: a.ordem)
                ],
            } for tarefa in tarefas
        ],
    }


def iniciar_nivelamento(usuario_id, competencia_id):
    try:
        bloquear_usuario(usuario_id)
        selecao = db.session.get(UsuarioCompetencia, (usuario_id, competencia_id))
        if selecao is None or not selecao.ativa:
            raise CompetenciaNaoSelecionada('Competência não selecionada pelo usuário.')
        aberta = db.session.scalar(db.select(AvaliacaoUsuario).where(
            AvaliacaoUsuario.usuario_id == usuario_id,
            AvaliacaoUsuario.competencia_id == competencia_id,
            AvaliacaoUsuario.status == 'em_andamento',
        ))
        if aberta is not None:
            if aberta.tipo != 'nivelamento':
                raise NivelamentoIndisponivel('Há uma reavaliação em andamento para esta competência.')
            resultado = serializar_avaliacao(aberta)
            db.session.commit()
            return resultado, 200
        concluida = db.session.scalar(db.select(AvaliacaoUsuario.id).where(
            AvaliacaoUsuario.usuario_id == usuario_id,
            AvaliacaoUsuario.competencia_id == competencia_id,
            AvaliacaoUsuario.tipo == 'nivelamento', AvaliacaoUsuario.status == 'concluida',
        ).limit(1))
        if concluida is not None:
            raise NivelamentoIndisponivel('O nivelamento desta competência já foi concluído.')
        tarefas = db.session.scalars(
            db.select(Tarefa).join(Habilidade, Habilidade.id == Tarefa.habilidade_id)
            .where(Habilidade.competencia_id == competencia_id)
            .options(selectinload(Tarefa.alternativas))
            .order_by(Habilidade.ordem, Habilidade.id, Tarefa.ordem, Tarefa.id)
        ).all()
        if not tarefas or any(len(t.alternativas) < 2 for t in tarefas):
            raise NivelamentoIndisponivel('Esta competência ainda não tem questões de nivelamento completas.')
        maximos = {t.id: max(a.pontuacao for a in t.alternativas) for t in tarefas}
        total = sum(maximos.values(), Decimal('0'))
        if total <= 0:
            raise NivelamentoIndisponivel('O nivelamento precisa ter pontuação máxima maior que zero.')
        avaliacao = AvaliacaoUsuario(usuario_id=usuario_id, competencia_id=competencia_id,
                                    tipo='nivelamento', status='em_andamento', pontuacao_maxima=total)
        db.session.add(avaliacao)
        db.session.flush()
        db.session.add_all([
            AvaliacaoTarefa(avaliacao_id=avaliacao.id, tarefa_id=t.id, pontuacao_maxima=maximos[t.id])
            for t in tarefas
        ])
        db.session.flush()
        resultado = serializar_avaliacao(avaliacao)
        db.session.commit()
        return resultado, 201
    except Exception:
        db.session.rollback()
        raise
