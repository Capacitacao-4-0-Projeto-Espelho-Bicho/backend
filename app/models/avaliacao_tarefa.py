"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class AvaliacaoTarefa(db.Model):
    __tablename__ = 'avaliacao_tarefa'
    avaliacao_id = db.Column(sa.INTEGER(), primary_key=True, nullable=False)
    tarefa_id = db.Column(sa.INTEGER(), primary_key=True, nullable=False)
    pontuacao_maxima = db.Column(sa.NUMERIC(precision=7, scale=2), nullable=False)
    __table_args__ = (
        sa.ForeignKeyConstraint(['avaliacao_id'], ['capacitacao.avaliacao_usuario.id'], name='avaliacao_tarefa_avaliacao_id_fkey'),
        sa.CheckConstraint('pontuacao_maxima >= 0::numeric', name='avaliacao_tarefa_pontuacao_maxima_check'),
        sa.ForeignKeyConstraint(['tarefa_id'], ['capacitacao.tarefa.id'], name='avaliacao_tarefa_tarefa_id_fkey'),
        {'schema': 'capacitacao'},
    )
