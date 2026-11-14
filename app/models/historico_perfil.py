"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class HistoricoPerfil(db.Model):
    __tablename__ = 'historico_perfil'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    usuario_id = db.Column(sa.INTEGER(), nullable=False)
    ambiente = db.Column(sa.VARCHAR(length=30), nullable=False)
    tempo = db.Column(sa.VARCHAR(length=30), nullable=False)
    recursos = db.Column(sa.VARCHAR(length=30), nullable=False)
    interlocutores = db.Column(sa.VARCHAR(length=30), nullable=False)
    origem = db.Column(sa.VARCHAR(length=30), nullable=False)
    motivo = db.Column(sa.TEXT(), nullable=True)
    data_registro = db.Column(sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    __table_args__ = (
        sa.ForeignKeyConstraint(['usuario_id'], ['capacitacao.usuario.id'], ondelete='CASCADE', name='historico_perfil_usuario_id_fkey'),
        {'schema': 'capacitacao'},
    )

    usuario = db.relationship("User", back_populates="historicos_perfil")
