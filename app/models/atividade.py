"""Modelo do schema capacitacao, alinhado a db/init.sql."""
import sqlalchemy as sa
from app.extensions import db


class Atividade(db.Model):
    __tablename__ = 'atividade'
    id = db.Column(sa.INTEGER(), sa.Identity(always=False), primary_key=True, nullable=False)
    nome = db.Column(sa.VARCHAR(length=200), nullable=False)
    competencia_id = db.Column(sa.INTEGER(), nullable=False)
    habilidade_id = db.Column(sa.INTEGER(), nullable=False)
    dificuldade = db.Column(sa.INTEGER(), nullable=False)
    duracao_min = db.Column(sa.INTEGER(), nullable=False)
    ambiente = db.Column(sa.VARCHAR(length=30), nullable=False, server_default=sa.text("'qualquer'::character varying"))
    tempo = db.Column(sa.VARCHAR(length=30), nullable=False, server_default=sa.text("'qualquer'::character varying"))
    recursos = db.Column(sa.VARCHAR(length=30), nullable=False, server_default=sa.text("'qualquer'::character varying"))
    interlocutores = db.Column(sa.VARCHAR(length=30), nullable=False, server_default=sa.text("'qualquer'::character varying"))
    descricao = db.Column(sa.TEXT(), nullable=True)
    data_criado = db.Column(sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    __table_args__ = (
        sa.ForeignKeyConstraint(['competencia_id'], ['capacitacao.competencia.id'], name='atividade_competencia_id_fkey'),
        sa.ForeignKeyConstraint(['dificuldade'], ['capacitacao.nivel.id'], name='atividade_dificuldade_fkey'),
        sa.CheckConstraint('duracao_min > 0', name='atividade_duracao_min_check'),
        sa.ForeignKeyConstraint(['habilidade_id'], ['capacitacao.habilidade.id'], name='atividade_habilidade_id_fkey'),
        sa.ForeignKeyConstraint(['habilidade_id', 'competencia_id'], ['capacitacao.habilidade.id', 'capacitacao.habilidade.competencia_id'], name='fk_atividade_habilidade_competencia'),
        sa.UniqueConstraint('id', 'competencia_id', name='uq_atividade_id_competencia'),
        {'schema': 'capacitacao'},
    )

    competencia = db.relationship("Competencia", back_populates="atividades", foreign_keys=[competencia_id])
    habilidade = db.relationship("Habilidade", foreign_keys=[habilidade_id])
    nivel = db.relationship("Nivel", foreign_keys=[dificuldade])
    questoes = db.relationship("AtividadeQuestao", back_populates="atividade", order_by="AtividadeQuestao.ordem")
