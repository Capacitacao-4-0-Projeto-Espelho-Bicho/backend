"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class FeedbackAtividade(db.Model):
    __tablename__ = 'feedback_atividade'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    execucao_id = db.Column(sa.INTEGER(), nullable=False)
    avaliacao_likert = db.Column(sa.SMALLINT(), nullable=False)
    comentario = db.Column(sa.TEXT(), nullable=True)
    data_registro = db.Column(sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    __table_args__ = (
        sa.CheckConstraint('avaliacao_likert >= 1 AND avaliacao_likert <= 5', name='feedback_atividade_avaliacao_likert_check'),
        sa.ForeignKeyConstraint(['execucao_id'], ['capacitacao.execucao.id'], name='feedback_atividade_execucao_id_fkey'),
        sa.UniqueConstraint('execucao_id', name='feedback_atividade_execucao_id_key'),
        {'schema': 'capacitacao'},
    )
