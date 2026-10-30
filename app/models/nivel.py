from app.extensions import db


class Nivel(db.Model):
    __tablename__ = "nivel"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text)

    ordem = db.Column(
        db.Integer,
        nullable=False,
        unique=True
    )

    perguntas = db.relationship(
        "Pergunta",
        back_populates="nivel"
    )