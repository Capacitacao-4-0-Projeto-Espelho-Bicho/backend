"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class OpcaoPergunta(db.Model):
    __tablename__ = 'opcao_pergunta'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    pergunta_id = db.Column(sa.INTEGER(), nullable=False)
    codigo = db.Column(sa.VARCHAR(length=50), nullable=False)
    texto = db.Column(sa.VARCHAR(length=255), nullable=False)
    valor = db.Column(sa.VARCHAR(length=100), nullable=True)
    ordem = db.Column(sa.INTEGER(), nullable=False)
    ativa = db.Column(sa.BOOLEAN(), nullable=False, server_default=sa.text('true'))
    __table_args__ = (
        sa.UniqueConstraint('id', 'pergunta_id', name='opcao_pergunta_id_pergunta_id_key'),
        sa.UniqueConstraint('pergunta_id', 'codigo', name='opcao_pergunta_pergunta_id_codigo_key'),
        sa.ForeignKeyConstraint(['pergunta_id'], ['capacitacao.pergunta.id'], name='opcao_pergunta_pergunta_id_fkey'),
        {'schema': 'capacitacao'},
    )
