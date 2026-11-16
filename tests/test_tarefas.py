"""Questões de nivelamento: autorização, validação e persistência atômica."""
from copy import deepcopy
from datetime import timedelta
import os
import unittest

from flask_jwt_extended import create_access_token, create_refresh_token
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User, Tarefa, Alternativa


@unittest.skipUnless(os.getenv('TEST_DATABASE_URL'), 'Requer PostgreSQL descartável')
class TarefasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({
            'TESTING': True, 'SQLALCHEMY_DATABASE_URI': os.environ['TEST_DATABASE_URL'],
            'JWT_SECRET_KEY': 'chave-exclusiva-de-testes-com-mais-de-32-caracteres',
        })
        cls.ctx = cls.app.app_context()
        cls.ctx.push()
        cls.client = cls.app.test_client()
        cls.ids = {}
        for papel in ('usuario', 'gestor', 'admin'):
            usuario = User(nome=papel, email=f'{papel}.tarefas@example.com',
                           senha_hash=generate_password_hash('senha-teste'), papel=papel)
            db.session.add(usuario)
            db.session.flush()
            cls.ids[papel] = usuario.id
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.engine.dispose()
        cls.ctx.pop()

    def headers(self, papel):
        return {'Authorization': 'Bearer ' + create_access_token(identity=str(self.ids[papel]))}

    def payload(self):
        return {
            'habilidade_id': 1, 'nivel_id': 1, 'enunciado': 'Como analisa processos?',
            'ordem': 1, 'alternativas': [
                {'texto': 'Analiso etapas e relações.', 'ordem': 2, 'pontuacao': 3.25, 'justificativa': 'Visão do contexto.'},
                {'texto': 'Observo só o resultado.', 'ordem': 1, 'pontuacao': 0},
            ],
        }

    def contagens(self):
        return tuple(db.session.scalar(db.select(sa.func.count()).select_from(modelo))
                     for modelo in (Tarefa, Alternativa))

    def test_admin_e_gestor_criam_questao_com_alternativas(self):
        for papel in ('admin', 'gestor'):
            before = self.contagens()
            response = self.client.post('/api/tarefas', json=self.payload(), headers=self.headers(papel))
            self.assertEqual(response.status_code, 201, response.json)
            self.assertEqual(self.contagens(), (before[0] + 1, before[1] + 2))
            dados = response.json
            self.assertEqual(dados['tempo_estimado_min'], 15)
            self.assertIsNone(dados['instrucoes'])
            self.assertEqual([a['ordem'] for a in dados['alternativas']], [1, 2])
            self.assertEqual(dados['alternativas'][1]['pontuacao'], 3.25)
            self.assertEqual(dados['alternativas'][1]['justificativa'], 'Visão do contexto.')
            db.session.expire_all()
            tarefa = db.session.get(Tarefa, dados['id'])
            self.assertEqual(tarefa.habilidade.competencia_id, 1)
            self.assertEqual(tarefa.nivel.id, 1)
            self.assertEqual(len(tarefa.alternativas), 2)
            self.assertTrue(all(a.tarefa_id == tarefa.id for a in tarefa.alternativas))

    def test_limite_cinco_alternativas_e_campos_opcionais(self):
        dados = self.payload()
        dados.update(nivel_id=4, instrucoes=' Escolha uma alternativa. ', tempo_estimado_min=7)
        dados['alternativas'] = [{'texto': f'Opção {i}', 'ordem': i, 'pontuacao': i-1} for i in range(5, 0, -1)]
        response = self.client.post('/api/tarefas', json=dados, headers=self.headers('gestor'))
        self.assertEqual(response.status_code, 201, response.json)
        self.assertEqual(response.json['nivel_id'], 4)
        self.assertEqual(response.json['tempo_estimado_min'], 7)
        self.assertEqual(response.json['instrucoes'], 'Escolha uma alternativa.')
        self.assertEqual([a['ordem'] for a in response.json['alternativas']], [1, 2, 3, 4, 5])

    def test_autenticacao_e_permissoes(self):
        before = self.contagens()
        self.assertEqual(self.client.post('/api/tarefas', json=self.payload()).status_code, 401)
        for token, status in (
            ('invalido', 422),
            (create_access_token(identity=str(self.ids['gestor']), expires_delta=timedelta(seconds=-1)), 401),
            (create_refresh_token(identity=str(self.ids['gestor'])), 422),
        ):
            self.assertEqual(self.client.post('/api/tarefas', json=self.payload(), headers={'Authorization': 'Bearer '+token}).status_code, status)
        self.assertEqual(self.client.post('/api/tarefas', json=self.payload(), headers=self.headers('usuario')).status_code, 403)
        self.assertEqual(self.contagens(), before)

    def test_usuario_inativo_ou_inexistente(self):
        usuario = db.session.get(User, self.ids['gestor'])
        usuario.ativo = False
        db.session.commit()
        try:
            self.assertEqual(self.client.post('/api/tarefas', json=self.payload(), headers=self.headers('gestor')).status_code, 401)
        finally:
            usuario.ativo = True
            db.session.commit()
        token = create_access_token(identity='999999')
        self.assertEqual(self.client.post('/api/tarefas', json=self.payload(), headers={'Authorization': 'Bearer '+token}).status_code, 401)

    def test_validacoes_sem_persistencia_parcial(self):
        casos = [None, [], {}, {'alternativas': [123]}]
        for campo, valor in (
            ('habilidade_id', 999999), ('nivel_id', 999999), ('habilidade_id', True),
            ('enunciado', ' '), ('enunciado', 1), ('ordem', 0), ('ordem', '1'),
            ('tempo_estimado_min', 0), ('tempo_estimado_min', None), ('instrucoes', []),
            ('alternativas', []), ('alternativas', [None]),
        ):
            dados = self.payload(); dados[campo] = valor; casos.append(dados)
        for campo, valor in (
            ('texto', ''), ('texto', None), ('ordem', 0), ('ordem', 6), ('ordem', True),
            ('pontuacao', -1), ('pontuacao', True), ('pontuacao', '3'),
            ('pontuacao', 0.001), ('pontuacao', 100000), ('pontuacao', float('nan')),
            ('pontuacao', float('inf')), ('justificativa', []),
        ):
            dados = self.payload(); dados['alternativas'][0][campo] = valor; casos.append(dados)
        dados = self.payload(); dados['alternativas'][0]['ordem'] = 1; casos.append(dados)
        dados = self.payload(); dados['alternativas'] = dados['alternativas'][:1]; casos.append(dados)
        dados = self.payload(); dados['alternativas'] = [deepcopy(dados['alternativas'][0]) for _ in range(6)]; casos.append(dados)
        dados = self.payload(); del dados['alternativas'][0]['pontuacao']; casos.append(dados)
        before = self.contagens()
        for dados in casos:
            with self.subTest(dados=dados):
                response = self.client.post('/api/tarefas', json=dados, headers=self.headers('gestor'))
                self.assertEqual(response.status_code, 400, response.json)
                self.assertEqual(self.contagens(), before)
        response = self.client.post('/api/tarefas', data='{', content_type='application/json', headers=self.headers('gestor'))
        self.assertEqual(response.status_code, 400)

    def test_erro_ao_inserir_alternativa_reverte_questao(self):
        before = self.contagens()
        def falhar(mapper, connection, target):
            self.assertEqual(connection.scalar(sa.select(sa.func.count()).select_from(Tarefa)), before[0] + 1)
            raise IntegrityError('Falha simulada na alternativa', {}, Exception('integridade'))
        sa.event.listen(Alternativa, 'before_insert', falhar)
        try:
            response = self.client.post('/api/tarefas', json=self.payload(), headers=self.headers('admin'))
            self.assertEqual(response.status_code, 409)
            self.assertEqual(self.contagens(), before)
        finally:
            sa.event.remove(Alternativa, 'before_insert', falhar)
        self.assertEqual(self.client.post('/api/tarefas', json=self.payload(), headers=self.headers('admin')).status_code, 201)

    def test_documentacao_swagger(self):
        response = self.client.get('/apispec_1.json')
        self.assertEqual(response.status_code, 200)
        operation = response.json['paths']['/api/tarefas']['post']
        self.assertEqual(operation['security'], [{'BearerAuth': []}])
        self.assertEqual(operation['tags'], ['Nivelamento'])
        for status in ('201', '400', '401', '403', '409', '422'):
            self.assertIn(status, operation['responses'])
        schema = operation['parameters'][0]['schema']
        self.assertEqual(schema['properties']['alternativas']['minItems'], 2)
        self.assertEqual(schema['properties']['alternativas']['maxItems'], 5)
        response = self.client.post('/api/tarefas', json=schema['example'], headers=self.headers('admin'))
        self.assertEqual(response.status_code, 201, response.json)
