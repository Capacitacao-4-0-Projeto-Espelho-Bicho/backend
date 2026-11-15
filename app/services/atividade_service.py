from decimal import Decimal, InvalidOperation

from app.extensions import db
from app.models import Atividade, AtividadeQuestao, AtividadeAlternativa, Competencia, Habilidade, Nivel


class DadosInvalidos(ValueError):
    pass


def inteiro(valor, campo):
    if type(valor) is not int or not 0 < valor <= 2147483647:
        raise DadosInvalidos(f'{campo} deve ser um inteiro positivo.')
    return valor


def texto(dados, campo, limite=None, obrigatorio=True):
    valor = dados.get(campo)
    if valor is None and not obrigatorio:
        return None
    if not isinstance(valor, str) or not valor.strip():
        raise DadosInvalidos(f'{campo} deve ser um texto não vazio.')
    valor = valor.strip()
    if limite and len(valor) > limite:
        raise DadosInvalidos(f'{campo} deve ter no máximo {limite} caracteres.')
    return valor


def lista(valor, campo, minimo=1):
    if not isinstance(valor, list) or len(valor) < minimo or any(not isinstance(v, dict) for v in valor):
        raise DadosInvalidos(f'{campo} deve conter pelo menos {minimo} objeto(s).')
    return valor


def ordens_unicas(itens, campo):
    ordens = [inteiro(item.get('ordem'), f'{campo}.ordem') for item in itens]
    if len(set(ordens)) != len(ordens):
        raise DadosInvalidos(f'{campo} contém ordens repetidas.')


def pontos(valor):
    if type(valor) not in (int, float):
        raise DadosInvalidos('pontuacao deve ser um número não negativo com até duas casas decimais.')
    try:
        numero = Decimal(str(valor))
        if not numero.is_finite() or numero < 0 or numero > Decimal('99999.99') or numero != numero.quantize(Decimal('0.01')):
            raise InvalidOperation
    except InvalidOperation:
        raise DadosInvalidos('pontuacao deve estar entre 0 e 99999.99 e ter até duas casas decimais.')
    return numero


def criar_atividade(dados):
    try:
        if not isinstance(dados, dict):
            raise DadosInvalidos('Envie um objeto JSON válido.')
        valores = {
            'nome': texto(dados, 'nome', 200),
            'descricao': texto(dados, 'descricao', obrigatorio=False),
        }
        for campo in ('competencia_id', 'habilidade_id', 'dificuldade', 'duracao_min'):
            valores[campo] = inteiro(dados.get(campo), campo)
        for campo in ('ambiente', 'tempo', 'recursos', 'interlocutores'):
            valores[campo] = texto(dados, campo, 30) if campo in dados else 'qualquer'
        if db.session.get(Competencia, valores['competencia_id']) is None:
            raise DadosInvalidos('Competência não encontrada.')
        habilidade = db.session.get(Habilidade, valores['habilidade_id'])
        if habilidade is None or habilidade.competencia_id != valores['competencia_id']:
            raise DadosInvalidos('A habilidade deve pertencer à competência informada.')
        if db.session.get(Nivel, valores['dificuldade']) is None:
            raise DadosInvalidos('Nível de dificuldade não encontrado.')
        questoes = lista(dados.get('questoes'), 'questoes')
        ordens_unicas(questoes, 'questoes')
        atividade = Atividade(**valores)
        for questao in questoes:
            alternativas = lista(questao.get('alternativas'), 'alternativas', minimo=2)
            ordens_unicas(alternativas, 'alternativas')
            modelo = AtividadeQuestao(
                enunciado=texto(questao, 'enunciado'),
                instrucoes=texto(questao, 'instrucoes', obrigatorio=False),
                ordem=questao['ordem'],
            )
            for alternativa in alternativas:
                modelo.alternativas.append(AtividadeAlternativa(
                    texto=texto(alternativa, 'texto'), ordem=alternativa['ordem'],
                    pontuacao=pontos(alternativa.get('pontuacao')),
                    justificativa=texto(alternativa, 'justificativa', obrigatorio=False),
                ))
            atividade.questoes.append(modelo)
        db.session.add(atividade)
        db.session.commit()
        return atividade
    except Exception:
        db.session.rollback()
        raise


def serializar_atividade(atividade, detalhe=False, editorial=False):
    dados = {campo: getattr(atividade, campo) for campo in (
        'id', 'nome', 'descricao', 'competencia_id', 'habilidade_id', 'dificuldade',
        'duracao_min', 'ambiente', 'tempo', 'recursos', 'interlocutores',
    )}
    if detalhe:
        dados['questoes'] = []
        for questao in sorted(atividade.questoes, key=lambda q: q.ordem):
            item = {campo: getattr(questao, campo) for campo in ('id', 'enunciado', 'instrucoes', 'ordem')}
            item['alternativas'] = []
            for alternativa in sorted(questao.alternativas, key=lambda a: a.ordem):
                opcao = {campo: getattr(alternativa, campo) for campo in ('id', 'texto', 'ordem')}
                if editorial:
                    opcao.update(pontuacao=float(alternativa.pontuacao), justificativa=alternativa.justificativa)
                item['alternativas'].append(opcao)
            dados['questoes'].append(item)
    return dados
