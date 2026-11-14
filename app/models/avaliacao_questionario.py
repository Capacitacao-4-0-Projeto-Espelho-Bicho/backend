"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class AvaliacaoQuestionario(db.Model):
    __tablename__ = 'avaliacao_questionario'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    usuario_id = db.Column(sa.INTEGER(), nullable=False)
    questionario_id = db.Column(sa.INTEGER(), nullable=False)
    tipo = db.Column(sa.VARCHAR(length=30), nullable=False, server_default=sa.text("'perfil'::character varying"))
    status = db.Column(sa.VARCHAR(length=20), nullable=False, server_default=sa.text("'em_andamento'::character varying"))
    data_inicio = db.Column(sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    data_conclusao = db.Column(sa.TIMESTAMP(), nullable=True)
    __table_args__ = (
        sa.UniqueConstraint('id', 'questionario_id', name='avaliacao_questionario_id_questionario_id_key'),
        sa.ForeignKeyConstraint(['questionario_id'], ['capacitacao.questionario.id'], name='avaliacao_questionario_questionario_id_fkey'),
        sa.CheckConstraint("status::text = ANY (ARRAY['em_andamento'::character varying, 'concluida'::character varying, 'cancelada'::character varying]::text[])", name='avaliacao_questionario_status_check'),
        sa.ForeignKeyConstraint(['usuario_id'], ['capacitacao.usuario.id'], name='avaliacao_questionario_usuario_id_fkey'),
        {'schema': 'capacitacao'},
    )
