"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class AvaliacaoUsuario(db.Model):
    __tablename__ = 'avaliacao_usuario'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    usuario_id = db.Column(sa.INTEGER(), nullable=False)
    competencia_id = db.Column(sa.INTEGER(), nullable=False)
    tipo = db.Column(sa.VARCHAR(length=30), nullable=False, server_default=sa.text("'nivelamento'::character varying"))
    status = db.Column(sa.VARCHAR(length=20), nullable=False, server_default=sa.text("'em_andamento'::character varying"))
    data_inicio = db.Column(sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    data_conclusao = db.Column(sa.TIMESTAMP(), nullable=True)
    pontuacao_total = db.Column(sa.NUMERIC(precision=12, scale=2), nullable=True)
    pontuacao_maxima = db.Column(sa.NUMERIC(precision=12, scale=2), nullable=True)
    percentual_pontuacao = db.Column(sa.NUMERIC(precision=5, scale=2), nullable=True)
    nivel_id = db.Column(sa.INTEGER(), nullable=True)
    __table_args__ = (
        sa.CheckConstraint('pontuacao_total <= pontuacao_maxima', name='avaliacao_usuario_check'),
        sa.UniqueConstraint('id', 'usuario_id', 'competencia_id', name='avaliacao_usuario_id_usuario_id_competencia_id_key'),
        sa.ForeignKeyConstraint(['nivel_id'], ['capacitacao.nivel.id'], name='avaliacao_usuario_nivel_id_fkey'),
        sa.CheckConstraint('percentual_pontuacao >= 0::numeric AND percentual_pontuacao <= 100::numeric', name='avaliacao_usuario_percentual_pontuacao_check'),
        sa.CheckConstraint('pontuacao_maxima > 0::numeric', name='avaliacao_usuario_pontuacao_maxima_check'),
        sa.CheckConstraint('pontuacao_total >= 0::numeric', name='avaliacao_usuario_pontuacao_total_check'),
        sa.CheckConstraint("status::text = ANY (ARRAY['em_andamento'::character varying, 'concluida'::character varying, 'cancelada'::character varying]::text[])", name='avaliacao_usuario_status_check'),
        sa.CheckConstraint("tipo::text = ANY (ARRAY['nivelamento'::character varying, 'reavaliacao'::character varying]::text[])", name='avaliacao_usuario_tipo_check'),
        sa.ForeignKeyConstraint(['usuario_id', 'competencia_id'], ['capacitacao.usuario_competencia.usuario_id', 'capacitacao.usuario_competencia.competencia_id'], name='avaliacao_usuario_usuario_id_competencia_id_fkey'),
        sa.Index('uq_avaliacao_aberta', 'usuario_id', 'competencia_id', unique=True, postgresql_where=sa.text("((status)::text = 'em_andamento'::text)")),
        {'schema': 'capacitacao'},
    )
