"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class RespostaTarefa(db.Model):
    __tablename__ = 'resposta_tarefa'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    avaliacao_id = db.Column(sa.INTEGER(), nullable=False)
    tarefa_id = db.Column(sa.INTEGER(), nullable=False)
    alternativa_id = db.Column(sa.INTEGER(), nullable=False)
    pontuacao_obtida = db.Column(sa.NUMERIC(precision=7, scale=2), nullable=False)
    tempo_gasto_seg = db.Column(sa.INTEGER(), nullable=True)
    data_resposta = db.Column(sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    __table_args__ = (
        sa.ForeignKeyConstraint(['alternativa_id', 'tarefa_id'], ['capacitacao.alternativa.id', 'capacitacao.alternativa.tarefa_id'], name='resposta_tarefa_alternativa_id_tarefa_id_fkey'),
        sa.ForeignKeyConstraint(['avaliacao_id', 'tarefa_id'], ['capacitacao.avaliacao_tarefa.avaliacao_id', 'capacitacao.avaliacao_tarefa.tarefa_id'], name='resposta_tarefa_avaliacao_id_tarefa_id_fkey'),
        sa.UniqueConstraint('avaliacao_id', 'tarefa_id', name='resposta_tarefa_avaliacao_id_tarefa_id_key'),
        sa.CheckConstraint('pontuacao_obtida >= 0::numeric', name='resposta_tarefa_pontuacao_obtida_check'),
        sa.CheckConstraint('tempo_gasto_seg >= 0', name='resposta_tarefa_tempo_gasto_seg_check'),
        {'schema': 'capacitacao'},
    )
