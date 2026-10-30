from app.extensions import db


class Competencia(db.Model):
    __tablename__ = "competencia"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)

    data_criado = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    perguntas = db.relationship(
        "Pergunta",
        back_populates="competencia"
    )

    atividades = db.relationship(
        "Atividade",
        back_populates="competencia"
    )

    niveis_usuarios = db.relationship(
        "NivelCompetencia",
        back_populates="competencia"
    )