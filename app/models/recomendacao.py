from app.extensions import db


class Recomendacao(db.Model):
    __tablename__ = "recomendacao"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False
    )

    atividade_id = db.Column(
        db.Integer,
        db.ForeignKey("atividade.id", ondelete="RESTRICT"),
        nullable=False
    )

    data_gerada = db.Column(
        db.Date,
        nullable=False,
        server_default=db.func.current_date()
    )

    regra_usada = db.Column(db.String(100), nullable=False)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="gerada",
        server_default="gerada"
    )

    motivo_recusa = db.Column(db.Text)
    data_decisao = db.Column(db.DateTime)

    usuario = db.relationship(
        "User",
        backref="recomendacoes"
    )

    atividade = db.relationship(
        "Atividade",
        back_populates="recomendacoes"
    )

    execucao = db.relationship(
        "Execucao",
        back_populates="recomendacao",
        uselist=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "usuario_id",
            "atividade_id",
            "data_gerada",
            name="uq_rec_dia"
        ),
        db.CheckConstraint(
            "status IN ('gerada', 'apresentada', 'aceite', 'recusada', 'expirada')",
            name="chk_rec_status"
        ),
    )