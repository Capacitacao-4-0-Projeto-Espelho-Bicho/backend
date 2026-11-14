"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class RespostaQuestionario(db.Model):
    __tablename__ = 'resposta_questionario'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    avaliacao_id = db.Column(sa.INTEGER(), nullable=False)
    questionario_id = db.Column(sa.INTEGER(), nullable=False)
    pergunta_id = db.Column(sa.INTEGER(), nullable=False)
    opcao_id = db.Column(sa.INTEGER(), nullable=True)
    resposta_texto = db.Column(sa.TEXT(), nullable=True)
    resposta_numero = db.Column(sa.NUMERIC(), nullable=True)
    data_resposta = db.Column(sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    __table_args__ = (
        sa.ForeignKeyConstraint(['avaliacao_id', 'questionario_id'], ['capacitacao.avaliacao_questionario.id', 'capacitacao.avaliacao_questionario.questionario_id'], name='resposta_questionario_avaliacao_id_questionario_id_fkey'),
        sa.CheckConstraint('num_nonnulls(opcao_id, resposta_texto, resposta_numero) = 1', name='resposta_questionario_check'),
        sa.ForeignKeyConstraint(['opcao_id', 'pergunta_id'], ['capacitacao.opcao_pergunta.id', 'capacitacao.opcao_pergunta.pergunta_id'], name='resposta_questionario_opcao_id_pergunta_id_fkey'),
        sa.ForeignKeyConstraint(['pergunta_id', 'questionario_id'], ['capacitacao.pergunta.id', 'capacitacao.pergunta.questionario_id'], name='resposta_questionario_pergunta_id_questionario_id_fkey'),
        {'schema': 'capacitacao'},
    )
