"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class Pergunta(db.Model):
    __tablename__ = 'pergunta'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    questionario_id = db.Column(sa.INTEGER(), nullable=False)
    titulo = db.Column(sa.VARCHAR(length=255), nullable=False)
    descricao = db.Column(sa.TEXT(), nullable=True)
    tipo = db.Column(sa.VARCHAR(length=30), nullable=False, server_default=sa.text("'unica'::character varying"))
    ordem = db.Column(sa.INTEGER(), nullable=False)
    obrigatoria = db.Column(sa.BOOLEAN(), nullable=False, server_default=sa.text('true'))
    campo_perfil = db.Column(sa.VARCHAR(length=30), nullable=True)
    __table_args__ = (
        sa.UniqueConstraint('id', 'questionario_id', name='pergunta_id_questionario_id_key'),
        sa.ForeignKeyConstraint(['questionario_id'], ['capacitacao.questionario.id'], name='pergunta_questionario_id_fkey'),
        sa.UniqueConstraint('questionario_id', 'ordem', name='pergunta_questionario_id_ordem_key'),
        sa.CheckConstraint("tipo::text = ANY (ARRAY['unica'::character varying, 'multipla'::character varying, 'texto'::character varying, 'numero'::character varying]::text[])", name='pergunta_tipo_check'),
        {'schema': 'capacitacao'},
    )
