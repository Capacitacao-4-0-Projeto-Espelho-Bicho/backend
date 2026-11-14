"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class Habilidade(db.Model):
    __tablename__ = 'habilidade'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    competencia_id = db.Column(sa.INTEGER(), nullable=False)
    nome = db.Column(sa.VARCHAR(length=200), nullable=False)
    descricao = db.Column(sa.TEXT(), nullable=True)
    ordem = db.Column(sa.INTEGER(), nullable=False)
    data_criado = db.Column(sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'))
    __table_args__ = (
        sa.ForeignKeyConstraint(['competencia_id'], ['capacitacao.competencia.id'], ondelete='CASCADE', name='fk_habilidade_competencia'),
        sa.UniqueConstraint('competencia_id', 'ordem', name='uq_habilidade_competencia_ordem'),
        sa.UniqueConstraint('id', 'competencia_id', name='uq_habilidade_id_competencia'),
        {'schema': 'capacitacao'},
    )

    competencia = db.relationship("Competencia", back_populates="habilidades")
    tarefas = db.relationship("Tarefa", back_populates="habilidade", order_by="Tarefa.ordem", passive_deletes=True)
