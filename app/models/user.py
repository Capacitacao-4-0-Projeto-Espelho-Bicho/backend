"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class User(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    nome = db.Column(sa.VARCHAR(length=150), nullable=False)
    email = db.Column(sa.VARCHAR(length=150), nullable=False)
    data_cadastro = db.Column(sa.TIMESTAMP(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'))
    senha_hash = db.Column(sa.TEXT(), nullable=False)
    ativo = db.Column(sa.BOOLEAN(), nullable=False, server_default=sa.text('true'))
    papel = db.Column(sa.VARCHAR(length=20), nullable=False, server_default=sa.text("'usuario'"))
    ultimo_login_em = db.Column(sa.TIMESTAMP(timezone=True), nullable=True)
    __table_args__ = (
        sa.CheckConstraint("papel IN ('usuario', 'gestor', 'admin')", name='chk_usuario_papel'),
        sa.UniqueConstraint('email', name='uq_usuario_email'),
        sa.Index('uq_usuario_email_normalizado', sa.text('lower(TRIM(BOTH FROM email))'), unique=True),
        {'schema': 'capacitacao'},
    )

    perfil = db.relationship("PerfilUsuario", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    historicos_perfil = db.relationship("HistoricoPerfil", back_populates="usuario", passive_deletes=True)
