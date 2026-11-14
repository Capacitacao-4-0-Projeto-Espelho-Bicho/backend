"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class RespostaAtividade(db.Model):
    __tablename__ = 'resposta_atividade'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    execucao_id = db.Column(sa.INTEGER(), nullable=False)
    questao_id = db.Column(sa.INTEGER(), nullable=False)
    alternativa_id = db.Column(sa.INTEGER(), nullable=False)
    pontuacao_obtida = db.Column(sa.NUMERIC(precision=7, scale=2), nullable=False)
    tempo_gasto_seg = db.Column(sa.INTEGER(), nullable=True)
    data_resposta = db.Column(sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    __table_args__ = (
        sa.ForeignKeyConstraint(['alternativa_id', 'questao_id'], ['capacitacao.atividade_alternativa.id', 'capacitacao.atividade_alternativa.questao_id'], name='resposta_atividade_alternativa_id_questao_id_fkey'),
        sa.ForeignKeyConstraint(['execucao_id', 'questao_id'], ['capacitacao.execucao_questao.execucao_id', 'capacitacao.execucao_questao.questao_id'], name='resposta_atividade_execucao_id_questao_id_fkey'),
        sa.UniqueConstraint('execucao_id', 'questao_id', name='resposta_atividade_execucao_id_questao_id_key'),
        sa.CheckConstraint('pontuacao_obtida >= 0::numeric', name='resposta_atividade_pontuacao_obtida_check'),
        sa.CheckConstraint('tempo_gasto_seg >= 0', name='resposta_atividade_tempo_gasto_seg_check'),
        {'schema': 'capacitacao'},
    )
