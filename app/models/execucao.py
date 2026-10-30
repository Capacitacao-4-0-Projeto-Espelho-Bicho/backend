from app.extensions import db


class Execucao(db.Model):
    __tablename__ = "execucao"

    id = db.Column(db.Integer, primary_key=True)

    recomendacao_id = db.Column(
        db.Integer,
        db.ForeignKey("recomendacao.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    evidencia_arquivo = db.Column(db.String(255))

    data_envio = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    feedback = db.Column(db.Text)

    progresso_atualizado = db.Column(db.Numeric(5, 2))

    recomendacao = db.relationship(
        "Recomendacao",
        back_populates="execucao"
    )

    __table_args__ = (
        db.CheckConstraint(
            "progresso_atualizado IS NULL OR "
            "(progresso_atualizado >= 0 AND progresso_atualizado <= 100)",
            name="chk_exec_progresso"
        ),
    )