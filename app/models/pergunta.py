from app.extensions import db


class Pergunta(db.Model):
    __tablename__ = "pergunta"

    id = db.Column(db.Integer, primary_key=True)

    competencia_id = db.Column(
        db.Integer,
        db.ForeignKey("competencia.id", ondelete="CASCADE"),
        nullable=False
    )

    nivel_id = db.Column(
        db.Integer,
        db.ForeignKey("nivel.id", ondelete="CASCADE"),
        nullable=False
    )

    texto = db.Column(db.Text, nullable=False)
    ordem = db.Column(db.Integer, nullable=False)

    data_criado = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    competencia = db.relationship(
        "Competencia",
        back_populates="perguntas"
    )

    nivel = db.relationship(
        "Nivel",
        back_populates="perguntas"
    )

    respostas = db.relationship(
        "Resposta",
        back_populates="pergunta"
    )