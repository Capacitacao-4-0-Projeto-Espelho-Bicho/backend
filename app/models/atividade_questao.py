"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class AtividadeQuestao(db.Model):
    __tablename__ = 'atividade_questao'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    atividade_id = db.Column(sa.INTEGER(), nullable=False)
    enunciado = db.Column(sa.TEXT(), nullable=False)
    instrucoes = db.Column(sa.TEXT(), nullable=True)
    ordem = db.Column(sa.INTEGER(), nullable=False)
    __table_args__ = (
        sa.ForeignKeyConstraint(['atividade_id'], ['capacitacao.atividade.id'], name='atividade_questao_atividade_id_fkey'),
        sa.UniqueConstraint('atividade_id', 'ordem', name='atividade_questao_atividade_id_ordem_key'),
        sa.UniqueConstraint('id', 'atividade_id', name='atividade_questao_id_atividade_id_key'),
        sa.CheckConstraint('ordem > 0', name='atividade_questao_ordem_check'),
        {'schema': 'capacitacao'},
    )

    atividade = db.relationship("Atividade", back_populates="questoes")
    alternativas = db.relationship("AtividadeAlternativa", back_populates="questao", order_by="AtividadeAlternativa.ordem")
