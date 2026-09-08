from app.extensions import db


class User(db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    senha = db.Column(db.String(255), nullable=False)

    ambiente = db.Column(db.String(30), nullable=False)
    tempo = db.Column(db.String(30), nullable=False)
    recursos = db.Column(db.String(30), nullable=False)
    interlocutores = db.Column(db.String(30), nullable=False)

    data_cadastro = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )