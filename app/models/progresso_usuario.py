"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class ProgressoUsuario(db.Model):
    __tablename__ = 'progresso_usuario'
    usuario_id = db.Column(sa.INTEGER(), primary_key=True, nullable=False)
    competencia_id = db.Column(sa.INTEGER(), primary_key=True, nullable=False)
    avaliacao_id = db.Column(sa.INTEGER(), nullable=False)
    nivel_atual = db.Column(sa.INTEGER(), nullable=False)
    pontuacao_total = db.Column(sa.NUMERIC(precision=12, scale=2), nullable=False)
    pontuacao_maxima = db.Column(sa.NUMERIC(precision=12, scale=2), nullable=False)
    total_tarefas = db.Column(sa.INTEGER(), nullable=False)
    percentual_pontuacao = db.Column(sa.NUMERIC(precision=5, scale=2), nullable=False)
    data_ultima_avaliacao = db.Column(sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    __table_args__ = (
        sa.UniqueConstraint('avaliacao_id', name='progresso_usuario_avaliacao_id_key'),
        sa.ForeignKeyConstraint(['avaliacao_id', 'usuario_id', 'competencia_id'], ['capacitacao.avaliacao_usuario.id', 'capacitacao.avaliacao_usuario.usuario_id', 'capacitacao.avaliacao_usuario.competencia_id'], name='progresso_usuario_avaliacao_id_usuario_id_competencia_id_fkey'),
        sa.CheckConstraint('pontuacao_total <= pontuacao_maxima', name='progresso_usuario_check'),
        sa.ForeignKeyConstraint(['nivel_atual'], ['capacitacao.nivel.id'], name='progresso_usuario_nivel_atual_fkey'),
        sa.CheckConstraint('percentual_pontuacao >= 0::numeric AND percentual_pontuacao <= 100::numeric', name='progresso_usuario_percentual_pontuacao_check'),
        sa.CheckConstraint('pontuacao_maxima > 0::numeric', name='progresso_usuario_pontuacao_maxima_check'),
        sa.CheckConstraint('pontuacao_total >= 0::numeric', name='progresso_usuario_pontuacao_total_check'),
        sa.CheckConstraint('total_tarefas > 0', name='progresso_usuario_total_tarefas_check'),
        {'schema': 'capacitacao'},
    )
