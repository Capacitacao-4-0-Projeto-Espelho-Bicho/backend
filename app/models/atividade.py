from app.extensions import db


class Atividade(db.Model):
    __tablename__ = "atividade"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(200), nullable=False)

    competencia_id = db.Column(
        db.Integer,
        db.ForeignKey("competencia.id", ondelete="RESTRICT"),
        nullable=False
    )

    dificuldade = db.Column(db.SmallInteger, nullable=False)
    duracao_min = db.Column(db.Integer, nullable=False)

    ambiente = db.Column(db.String(30), nullable=False)
    tempo = db.Column(db.String(30), nullable=False)
    recursos = db.Column(db.String(30), nullable=False)
    interlocutores = db.Column(db.String(30), nullable=False)

    evidencia_exigida = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text)

    data_criado = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    competencia = db.relationship(
        "Competencia",
        back_populates="atividades"
    )

    recomendacoes = db.relationship(
        "Recomendacao",
        back_populates="atividade"
    )

    __table_args__ = (
        db.CheckConstraint(
            "dificuldade BETWEEN 1 AND 3",
            name="chk_atv_dificuldade"
        ),
        db.CheckConstraint(
            "duracao_min > 0",
            name="chk_atv_duracao"
        ),
        db.CheckConstraint(
            "ambiente IN ('individual', 'em_aula', 'em_equipe', 'no_trabalho')",
            name="chk_atv_ambiente"
        ),
        db.CheckConstraint(
            "tempo IN ('ate_15_min', '15_a_45_min', 'mais_45_min')",
            name="chk_atv_tempo"
        ),
        db.CheckConstraint(
            "recursos IN ('nenhum', 'papel_ou_celular', 'computador')",
            name="chk_atv_recursos"
        ),
        db.CheckConstraint(
            "interlocutores IN ('sozinho', 'com_colega', 'com_grupo')",
            name="chk_atv_interlocutores"
        ),
        db.CheckConstraint(
            "evidencia_exigida IN ('texto', 'arquivo', 'registro_conclusao')",
            name="chk_atv_evidencia"
        ),
    )