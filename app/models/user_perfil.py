"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class PerfilUsuario(db.Model):
    __tablename__ = 'perfil_usuario'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    usuario_id = db.Column(sa.INTEGER(), nullable=False)
    ambiente = db.Column(sa.VARCHAR(length=30), nullable=False)
    tempo = db.Column(sa.VARCHAR(length=30), nullable=False)
    recursos = db.Column(sa.VARCHAR(length=30), nullable=False)
    interlocutores = db.Column(sa.VARCHAR(length=30), nullable=False)
    origem_atualizacao = db.Column(sa.VARCHAR(length=30), nullable=False, server_default=sa.text("'onboarding'::character varying"))
    atualizado_em = db.Column(sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    __table_args__ = (
        sa.ForeignKeyConstraint(['usuario_id'], ['capacitacao.usuario.id'], ondelete='CASCADE', name='perfil_usuario_usuario_id_fkey'),
        sa.UniqueConstraint('usuario_id', name='perfil_usuario_usuario_id_key'),
        {'schema': 'capacitacao'},
    )

    usuario = db.relationship("User", back_populates="perfil")
