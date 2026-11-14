"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class Nivel(db.Model):
    __tablename__ = 'nivel'
    id = db.Column(sa.INTEGER(), primary_key=True, nullable=False)
    nome = db.Column(sa.VARCHAR(length=50), nullable=False)
    descricao = db.Column(sa.TEXT(), nullable=True)
    ordem = db.Column(sa.INTEGER(), nullable=False)
    pontuacao_minima = db.Column(sa.NUMERIC(precision=5, scale=2), nullable=False)
    pontuacao_maxima = db.Column(sa.NUMERIC(precision=5, scale=2), nullable=False)
    __table_args__ = (
        sa.CheckConstraint('ordem >= 1 AND ordem <= 4', name='chk_nivel_ordem'),
        sa.CheckConstraint('pontuacao_minima >= 0::numeric AND pontuacao_maxima <= 100::numeric', name='chk_pontuacao'),
        sa.UniqueConstraint('ordem', name='nivel_ordem_key'),
        {'schema': 'capacitacao'},
    )

    tarefas = db.relationship("Tarefa", back_populates="nivel")
