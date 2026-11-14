"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class Competencia(db.Model):
    __tablename__ = 'competencia'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    nome = db.Column(sa.VARCHAR(length=100), nullable=False)
    descricao = db.Column(sa.TEXT(), nullable=True)
    data_criado = db.Column(sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'))
    __table_args__ = (
        sa.UniqueConstraint('nome', name='uq_competencia_nome'),
        {'schema': 'capacitacao'},
    )

    habilidades = db.relationship("Habilidade", back_populates="competencia", order_by="Habilidade.ordem", passive_deletes=True)
    atividades = db.relationship("Atividade", back_populates="competencia", foreign_keys="Atividade.competencia_id")
