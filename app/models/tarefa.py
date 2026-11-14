"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class Tarefa(db.Model):
    __tablename__ = 'tarefa'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    habilidade_id = db.Column(sa.INTEGER(), nullable=False)
    nivel_id = db.Column(sa.INTEGER(), nullable=False)
    enunciado = db.Column(sa.TEXT(), nullable=False)
    instrucoes = db.Column(sa.TEXT(), nullable=True)
    ordem = db.Column(sa.INTEGER(), nullable=False)
    tempo_estimado_min = db.Column(sa.INTEGER(), nullable=True, server_default=sa.text('15'))
    data_criado = db.Column(sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'))
    __table_args__ = (
        sa.CheckConstraint('ordem > 0', name='chk_tarefa_ordem'),
        sa.ForeignKeyConstraint(['habilidade_id'], ['capacitacao.habilidade.id'], ondelete='CASCADE', name='fk_tarefa_habilidade'),
        sa.ForeignKeyConstraint(['nivel_id'], ['capacitacao.nivel.id'], ondelete='RESTRICT', name='fk_tarefa_nivel'),
        sa.Index('idx_tarefa_habilidade', 'habilidade_id', unique=False),
        {'schema': 'capacitacao'},
    )

    habilidade = db.relationship("Habilidade", back_populates="tarefas")
    nivel = db.relationship("Nivel", back_populates="tarefas")
    alternativas = db.relationship("Alternativa", back_populates="tarefa", order_by="Alternativa.ordem", passive_deletes=True)
