
from app.extensions import db


class PerfilUsuario(db.Model):
    __tablename__ = "perfil_usuario"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    ambiente = db.Column(db.String(30), nullable=False)
    tempo = db.Column(db.String(30), nullable=False)
    recursos = db.Column(db.String(30), nullable=False)
    interlocutores = db.Column(db.String(30), nullable=False)

    origem_atualizacao = db.Column(
        db.String(30),
        nullable=False,
        default="onboarding",
        server_default="onboarding"
    )

    atualizado_em = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )
