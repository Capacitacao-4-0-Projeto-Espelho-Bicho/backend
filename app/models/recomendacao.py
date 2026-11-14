"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class Recomendacao(db.Model):
    __tablename__ = 'recomendacao'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    usuario_id = db.Column(sa.INTEGER(), nullable=False)
    atividade_id = db.Column(sa.INTEGER(), nullable=False)
    avaliacao_id = db.Column(sa.INTEGER(), nullable=False)
    data_gerada = db.Column(sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    regra_usada = db.Column(sa.VARCHAR(length=100), nullable=False)
    status = db.Column(sa.VARCHAR(length=20), nullable=False, server_default=sa.text("'gerada'::character varying"))
    motivo_recusa = db.Column(sa.TEXT(), nullable=True)
    data_decisao = db.Column(sa.TIMESTAMP(), nullable=True)
    competencia_id = db.Column(sa.INTEGER(), nullable=False)
    __table_args__ = (
        sa.ForeignKeyConstraint(['atividade_id', 'competencia_id'], ['capacitacao.atividade.id', 'capacitacao.atividade.competencia_id'], name='fk_recomendacao_atividade_competencia'),
        sa.ForeignKeyConstraint(['avaliacao_id', 'usuario_id', 'competencia_id'], ['capacitacao.avaliacao_usuario.id', 'capacitacao.avaliacao_usuario.usuario_id', 'capacitacao.avaliacao_usuario.competencia_id'], name='fk_recomendacao_avaliacao_usuario'),
        sa.ForeignKeyConstraint(['atividade_id'], ['capacitacao.atividade.id'], name='recomendacao_atividade_id_fkey'),
        sa.ForeignKeyConstraint(['avaliacao_id'], ['capacitacao.avaliacao_usuario.id'], name='recomendacao_avaliacao_id_fkey'),
        sa.CheckConstraint("status::text = ANY (ARRAY['gerada'::character varying, 'aceita'::character varying, 'recusada'::character varying, 'em_andamento'::character varying, 'concluida'::character varying, 'cancelada'::character varying]::text[])", name='recomendacao_status_check'),
        sa.UniqueConstraint('usuario_id', 'atividade_id', 'avaliacao_id', name='recomendacao_usuario_id_atividade_id_avaliacao_id_key'),
        sa.ForeignKeyConstraint(['usuario_id'], ['capacitacao.usuario.id'], name='recomendacao_usuario_id_fkey'),
        sa.UniqueConstraint('id', 'atividade_id', name='uq_recomendacao_id_atividade'),
        sa.Index('idx_recomendacao_usuario_status', 'usuario_id', 'status', unique=False),
        {'schema': 'capacitacao'},
    )
