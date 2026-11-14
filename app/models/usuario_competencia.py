"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class UsuarioCompetencia(db.Model):
    __tablename__ = 'usuario_competencia'
    usuario_id = db.Column(sa.INTEGER(), primary_key=True, nullable=False)
    competencia_id = db.Column(sa.INTEGER(), primary_key=True, nullable=False)
    selecionada_em = db.Column(sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    ativa = db.Column(sa.BOOLEAN(), nullable=False, server_default=sa.text('true'))
    __table_args__ = (
        sa.ForeignKeyConstraint(['competencia_id'], ['capacitacao.competencia.id'], name='usuario_competencia_competencia_id_fkey'),
        sa.ForeignKeyConstraint(['usuario_id'], ['capacitacao.usuario.id'], ondelete='CASCADE', name='usuario_competencia_usuario_id_fkey'),
        {'schema': 'capacitacao'},
    )
