from app.extensions import db


class Resposta(db.Model):
    __tablename__ = "resposta"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False
    )

    pergunta_id = db.Column(
        db.Integer,
        db.ForeignKey("pergunta.id", ondelete="CASCADE"),
        nullable=False
    )

    resposta = db.Column(db.Boolean, nullable=False)

    data_resposta = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    usuario = db.relationship(
        "User",
        backref="respostas"
    )

    pergunta = db.relationship(
        "Pergunta",
        back_populates="respostas"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "usuario_id",
            "pergunta_id",
            name="uq_resposta_usuario_pergunta"
        ),
    )