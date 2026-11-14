from flask import Blueprint, jsonify

from app.extensions import db
from app.models import Competencia, Habilidade, Nivel


catalogo_bp = Blueprint("catalogo", __name__)


@catalogo_bp.get("/competencias")
def listar_competencias():
    """
    Lista as competências disponíveis.
    ---
    tags:
      - Competências
    summary: Listar competências
    description: Retorna todas as competências em ordem de ID. Requer token JWT de acesso.
    produces:
      - application/json
    security:
      - BearerAuth: []
    responses:
      200:
        description: Lista de competências. Retorna uma lista vazia se não houver cadastros.
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              nome:
                type: string
                example: Pensamento Crítico e Inovação
              descricao:
                type: string
                x-nullable: true
                example: Capacidade de analisar argumentos e gerar soluções criativas.
      401:
        description: Token JWT ausente ou expirado.
      422:
        description: Token JWT inválido ou de tipo diferente de acesso.
    """
    competencias = db.session.scalars(
        db.select(Competencia).order_by(Competencia.id)
    ).all()
    return jsonify([
        {"id": item.id, "nome": item.nome, "descricao": item.descricao}
        for item in competencias
    ]), 200


@catalogo_bp.get("/competencias/<int:competencia_id>/habilidades")
def listar_habilidades(competencia_id):
    """
    Lista as habilidades de uma competência.
    ---
    tags:
      - Competências
    summary: Listar habilidades da competência
    description: Retorna as habilidades por ordem crescente do campo ordem. Requer token JWT de acesso.
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: competencia_id
        required: true
        type: integer
        minimum: 1
        description: ID da competência.
        example: 1
    responses:
      200:
        description: Lista de habilidades. Uma competência sem habilidades retorna uma lista vazia.
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              competencia_id:
                type: integer
                example: 1
              nome:
                type: string
                example: Descrever elementos de um processo contextualizando-os
              descricao:
                type: string
                x-nullable: true
                example: Capacidade de mapear processos em seu contexto real.
              ordem:
                type: integer
                example: 1
      401:
        description: Token JWT ausente ou expirado.
      404:
        description: Competência não encontrada.
        schema:
          type: object
          properties:
            error:
              type: string
              example: Competência não encontrada.
      422:
        description: Token JWT inválido ou de tipo diferente de acesso.
    """
    if db.session.get(Competencia, competencia_id) is None:
        return jsonify({"error": "Competência não encontrada."}), 404

    habilidades = db.session.scalars(
        db.select(Habilidade)
        .where(Habilidade.competencia_id == competencia_id)
        .order_by(Habilidade.ordem)
    ).all()
    return jsonify([
        {
            "id": item.id,
            "competencia_id": item.competencia_id,
            "nome": item.nome,
            "descricao": item.descricao,
            "ordem": item.ordem,
        }
        for item in habilidades
    ]), 200


@catalogo_bp.get("/niveis")
def listar_niveis():
    """
    Lista os níveis de desenvolvimento.
    ---
    tags:
      - Níveis
    summary: Listar níveis
    description: Retorna os quatro níveis do catálogo inicial por ordem crescente, com suas faixas de pontuação. Requer token JWT de acesso.
    produces:
      - application/json
    security:
      - BearerAuth: []
    responses:
      200:
        description: Lista de níveis cadastrados, de Iniciante a Avançado.
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              nome:
                type: string
                example: Iniciante
              descricao:
                type: string
                x-nullable: true
                example: Reconhece conceitos básicos e demonstra conscientização inicial.
              ordem:
                type: integer
                example: 1
              pontuacao_minima:
                type: number
                format: double
                example: 0.00
              pontuacao_maxima:
                type: number
                format: double
                example: 25.00
      401:
        description: Token JWT ausente ou expirado.
      422:
        description: Token JWT inválido ou de tipo diferente de acesso.
    """
    niveis = db.session.scalars(db.select(Nivel).order_by(Nivel.ordem)).all()
    return jsonify([
        {
            "id": item.id,
            "nome": item.nome,
            "descricao": item.descricao,
            "ordem": item.ordem,
            "pontuacao_minima": float(item.pontuacao_minima),
            "pontuacao_maxima": float(item.pontuacao_maxima),
        }
        for item in niveis
    ]), 200
