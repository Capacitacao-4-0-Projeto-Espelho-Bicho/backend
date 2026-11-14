"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class Alternativa(db.Model):
    __tablename__ = 'alternativa'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    tarefa_id = db.Column(sa.INTEGER(), nullable=False)
    texto = db.Column(sa.TEXT(), nullable=False)
    ordem = db.Column(sa.INTEGER(), nullable=False)
    pontuacao = db.Column(sa.NUMERIC(precision=7, scale=2), nullable=False, server_default=sa.text('0'))
    justificativa = db.Column(sa.TEXT(), nullable=True)
    data_criado = db.Column(sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'))
    __table_args__ = (
        sa.CheckConstraint('pontuacao >= 0::numeric', name='alternativa_pontuacao_check'),
        sa.CheckConstraint('ordem >= 1 AND ordem <= 5', name='chk_alternativa_quantidade'),
        sa.ForeignKeyConstraint(['tarefa_id'], ['capacitacao.tarefa.id'], ondelete='CASCADE', name='fk_alternativa_tarefa'),
        sa.UniqueConstraint('id', 'tarefa_id', name='uq_alternativa_id_tarefa'),
        sa.UniqueConstraint('tarefa_id', 'ordem', name='uq_alternativa_tarefa_ordem'),
        {'schema': 'capacitacao'},
    )

    tarefa = db.relationship("Tarefa", back_populates="alternativas")
