"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class ExecucaoQuestao(db.Model):
    __tablename__ = 'execucao_questao'
    execucao_id = db.Column(sa.INTEGER(), primary_key=True, nullable=False)
    atividade_id = db.Column(sa.INTEGER(), nullable=False)
    questao_id = db.Column(sa.INTEGER(), primary_key=True, nullable=False)
    pontuacao_maxima = db.Column(sa.NUMERIC(precision=7, scale=2), nullable=False)
    __table_args__ = (
        sa.ForeignKeyConstraint(['execucao_id', 'atividade_id'], ['capacitacao.execucao.id', 'capacitacao.execucao.atividade_id'], name='execucao_questao_execucao_id_atividade_id_fkey'),
        sa.CheckConstraint('pontuacao_maxima >= 0::numeric', name='execucao_questao_pontuacao_maxima_check'),
        sa.ForeignKeyConstraint(['questao_id', 'atividade_id'], ['capacitacao.atividade_questao.id', 'capacitacao.atividade_questao.atividade_id'], name='execucao_questao_questao_id_atividade_id_fkey'),
        {'schema': 'capacitacao'},
    )
