"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class Questionario(db.Model):
    __tablename__ = 'questionario'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    nome = db.Column(sa.VARCHAR(length=150), nullable=False)
    descricao = db.Column(sa.TEXT(), nullable=True)
    ativo = db.Column(sa.BOOLEAN(), nullable=False, server_default=sa.text('true'))
    data_criacao = db.Column(sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    __table_args__ = (
        {'schema': 'capacitacao'},
    )
