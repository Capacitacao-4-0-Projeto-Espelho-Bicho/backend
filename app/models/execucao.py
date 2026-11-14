"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class Execucao(db.Model):
    __tablename__ = 'execucao'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    recomendacao_id = db.Column(sa.INTEGER(), nullable=False)
    atividade_id = db.Column(sa.INTEGER(), nullable=False)
    status = db.Column(sa.VARCHAR(length=20), nullable=False, server_default=sa.text("'em_andamento'::character varying"))
    data_inicio = db.Column(sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    data_conclusao = db.Column(sa.TIMESTAMP(), nullable=True)
    pontuacao_total = db.Column(sa.NUMERIC(precision=12, scale=2), nullable=True)
    pontuacao_maxima = db.Column(sa.NUMERIC(precision=12, scale=2), nullable=True)
    percentual_pontuacao = db.Column(sa.NUMERIC(precision=5, scale=2), nullable=True)
    __table_args__ = (
        sa.ForeignKeyConstraint(['atividade_id'], ['capacitacao.atividade.id'], name='execucao_atividade_id_fkey'),
        sa.CheckConstraint('pontuacao_total <= pontuacao_maxima', name='execucao_check'),
        sa.UniqueConstraint('id', 'atividade_id', name='execucao_id_atividade_id_key'),
        sa.CheckConstraint('percentual_pontuacao >= 0::numeric AND percentual_pontuacao <= 100::numeric', name='execucao_percentual_pontuacao_check'),
        sa.CheckConstraint('pontuacao_maxima > 0::numeric', name='execucao_pontuacao_maxima_check'),
        sa.CheckConstraint('pontuacao_total >= 0::numeric', name='execucao_pontuacao_total_check'),
        sa.ForeignKeyConstraint(['recomendacao_id'], ['capacitacao.recomendacao.id'], name='execucao_recomendacao_id_fkey'),
        sa.UniqueConstraint('recomendacao_id', name='execucao_recomendacao_id_key'),
        sa.CheckConstraint("status::text = ANY (ARRAY['em_andamento'::character varying, 'concluida'::character varying, 'cancelada'::character varying]::text[])", name='execucao_status_check'),
        sa.ForeignKeyConstraint(['recomendacao_id', 'atividade_id'], ['capacitacao.recomendacao.id', 'capacitacao.recomendacao.atividade_id'], name='fk_execucao_recomendacao_atividade'),
        {'schema': 'capacitacao'},
    )
