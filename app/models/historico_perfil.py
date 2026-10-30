from app.extensions import db


class HistoricoPerfil(db.Model):
    __tablename__ = "historico_perfil"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False
    )

    ambiente = db.Column(db.String(30), nullable=False)
    tempo = db.Column(db.String(30), nullable=False)
    recursos = db.Column(db.String(30), nullable=False)
    interlocutores = db.Column(db.String(30), nullable=False)

    origem = db.Column(db.String(30), nullable=False)
    motivo = db.Column(db.Text)

    data_registro = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    usuario = db.relationship(
        "User",
        backref="historicos_perfil"
    )