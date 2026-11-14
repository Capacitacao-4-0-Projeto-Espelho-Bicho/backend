"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class AtividadeAlternativa(db.Model):
    __tablename__ = 'atividade_alternativa'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    questao_id = db.Column(sa.INTEGER(), nullable=False)
    texto = db.Column(sa.TEXT(), nullable=False)
    ordem = db.Column(sa.INTEGER(), nullable=False)
    pontuacao = db.Column(sa.NUMERIC(precision=7, scale=2), nullable=False, server_default=sa.text('0'))
    justificativa = db.Column(sa.TEXT(), nullable=True)
    __table_args__ = (
        sa.UniqueConstraint('id', 'questao_id', name='atividade_alternativa_id_questao_id_key'),
        sa.CheckConstraint('ordem > 0', name='atividade_alternativa_ordem_check'),
        sa.CheckConstraint('pontuacao >= 0::numeric', name='atividade_alternativa_pontuacao_check'),
        sa.ForeignKeyConstraint(['questao_id'], ['capacitacao.atividade_questao.id'], name='atividade_alternativa_questao_id_fkey'),
        sa.UniqueConstraint('questao_id', 'ordem', name='atividade_alternativa_questao_id_ordem_key'),
        {'schema': 'capacitacao'},
    )

    questao = db.relationship("AtividadeQuestao", back_populates="alternativas")
