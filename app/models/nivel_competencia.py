from app.extensions import db


class NivelCompetencia(db.Model):
    __tablename__ = "nivel_competencia"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False
    )

    competencia_id = db.Column(
        db.Integer,
        db.ForeignKey("competencia.id", ondelete="RESTRICT"),
        nullable=False
    )

    nivel = db.Column(db.Numeric(3, 2), nullable=False)

    percentual_acerto = db.Column(
        db.Numeric(5, 2),
        nullable=False
    )

    data_avaliacao = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    usuario = db.relationship(
        "User",
        backref="niveis_competencia"
    )

    competencia = db.relationship(
        "Competencia",
        back_populates="niveis_usuarios"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "usuario_id",
            "competencia_id",
            name="uq_nivel_usuario_competencia"
        ),
        db.CheckConstraint(
            "nivel BETWEEN 1.00 AND 4.00",
            name="chk_nivel_valor"
        ),
        db.CheckConstraint(
            "percentual_acerto BETWEEN 0.00 AND 100.00",
            name="chk_percentual"
        ),
    )