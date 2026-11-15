"""Integração do cadastro atômico e dos perfis, em PostgreSQL descartável."""
from copy import deepcopy
import os
from pathlib import Path
import unittest

from flask_jwt_extended import create_access_token
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User, Atividade, AtividadeQuestao, AtividadeAlternativa


@unittest.skipUnless(os.getenv('TEST_DATABASE_URL'), 'Requer PostgreSQL descartável')
class AtividadesTest(unittest.TestCase):
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
            user = User(nome=papel, email=f'{papel}.atividades@example.com',
                        senha_hash=generate_password_hash('senha-teste'), papel=papel)
            db.session.add(user)
            db.session.flush()
            cls.ids[papel] = user.id
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.engine.dispose()
        cls.ctx.pop()

    def headers(self, papel):
        return {'Authorization': 'Bearer ' + create_access_token(identity=str(self.ids[papel]))}

    def payload(self):
        return dict(nome='Atividade de teste', competencia_id=1, habilidade_id=1,
                    dificuldade=4, duracao_min=15, questoes=[{
                        'enunciado': 'Como você analisa processos?', 'ordem': 1,
                        'alternativas': [
                            {'texto': 'Observo as relações.', 'ordem': 2, 'pontuacao': 3.25, 'justificativa': 'Considera o contexto.'},
                            {'texto': 'Observo uma etapa.', 'ordem': 1, 'pontuacao': 0},
                        ],
                    }])

    def contagens(self):
        return tuple(db.session.scalar(db.select(sa.func.count()).select_from(m))
                     for m in (Atividade, AtividadeQuestao, AtividadeAlternativa))

    def test_criacao_e_leitura_por_papel(self):
        for papel in ('gestor', 'admin'):
            with self.subTest(papel=papel):
                response = self.client.post('/api/atividades', json=self.payload(), headers=self.headers(papel))
                self.assertEqual(response.status_code, 201, response.json)
                dados = response.json
                self.assertEqual(dados['ambiente'], 'qualquer')
                self.assertEqual(dados['dificuldade'], 4)
                self.assertEqual([a['ordem'] for a in dados['questoes'][0]['alternativas']], [1, 2])
                self.assertEqual(dados['questoes'][0]['alternativas'][1]['pontuacao'], 3.25)
                route = f"/api/atividades/{dados['id']}"
                user_response = self.client.get(route, headers=self.headers('usuario'))
                self.assertEqual(user_response.status_code, 200)
                for alternativa in user_response.json['questoes'][0]['alternativas']:
                    self.assertNotIn('pontuacao', alternativa)
                    self.assertNotIn('justificativa', alternativa)
                editorial = self.client.get(route, headers=self.headers(papel))
                self.assertIn('pontuacao', editorial.json['questoes'][0]['alternativas'][0])
                listed = self.client.get('/api/atividades?competencia_id=1&dificuldade=4', headers=self.headers('usuario'))
                self.assertEqual(listed.status_code, 200)
                self.assertIn(dados['id'], [a['id'] for a in listed.json])
                self.assertTrue(all('questoes' not in a for a in listed.json))

    def test_usuario_nao_pode_criar_nem_alterar_papeis(self):
        before = self.contagens()
        response = self.client.post('/api/atividades', json=self.payload(), headers=self.headers('usuario'))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.contagens(), before)
        route = f"/api/usuarios/{self.ids['usuario']}/papel"
        for papel in ('usuario', 'gestor'):
            self.assertEqual(self.client.patch(route, json={'papel': 'admin'}, headers=self.headers(papel)).status_code, 403)

    def test_admin_altera_papel_com_efeito_em_token_existente(self):
        route = f"/api/usuarios/{self.ids['usuario']}/papel"
        token_original = self.headers('usuario')
        try:
            response = self.client.patch(route, json={'papel': 'gestor'}, headers=self.headers('admin'))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['papel'], 'gestor')
            self.assertEqual(self.client.post('/api/atividades', json=self.payload(), headers=token_original).status_code, 201)
            self.client.patch(route, json={'papel': 'usuario'}, headers=self.headers('admin'))
            self.assertEqual(self.client.post('/api/atividades', json=self.payload(), headers=token_original).status_code, 403)
            self.assertEqual(self.client.patch(route, json={'papel': 'superadmin'}, headers=self.headers('admin')).status_code, 400)
            self.assertEqual(self.client.patch('/api/usuarios/999999/papel', json={'papel': 'gestor'}, headers=self.headers('admin')).status_code, 404)
        finally:
            db.session.get(User, self.ids['usuario']).papel = 'usuario'
            db.session.commit()

    def test_cadastro_publico_nao_eleva_permissoes(self):
        response = self.client.post('/api/auth/register', json={
            'nome': 'Novo', 'email': 'sem.elevacao@example.com', 'senha': 'teste',
            'ambiente': 'individual', 'tempo': 'ate_15_min', 'recursos': 'nenhum',
            'interlocutores': 'sozinho', 'papel': 'admin',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.query.filter_by(email='sem.elevacao@example.com').one().papel, 'usuario')

    def test_validacoes_nao_deixam_registros_parciais(self):
        casos = []
        for campo, valor in (('nome', ''), ('nome', 'a'*201), ('competencia_id', 999999),
                             ('habilidade_id', 7), ('dificuldade', 5), ('duracao_min', 0),
                             ('duracao_min', True), ('questoes', []), ('ambiente', 'a'*31)):
            dados = self.payload(); dados[campo] = valor; casos.append(dados)
        for campo, valor in (('pontuacao', -1), ('pontuacao', 0.001), ('pontuacao', True),
                             ('pontuacao', 100000), ('pontuacao', '3'), ('ordem', 0)):
            dados = self.payload(); dados['questoes'][0]['alternativas'][0][campo] = valor; casos.append(dados)
        dados = self.payload(); dados['questoes'][0]['alternativas'][0]['ordem'] = 1; casos.append(dados)
        dados = self.payload(); dados['questoes'].append(deepcopy(dados['questoes'][0])); casos.append(dados)
        dados = self.payload(); dados['questoes'][0]['alternativas'] = dados['questoes'][0]['alternativas'][:1]; casos.append(dados)
        dados = self.payload(); del dados['questoes'][0]['alternativas'][0]['pontuacao']; casos.append(dados)
        casos += [None, [], {'questoes': [123]}]
        before = self.contagens()
        for dados in casos:
            with self.subTest(dados=dados):
                response = self.client.post('/api/atividades', json=dados, headers=self.headers('gestor'))
                self.assertEqual(response.status_code, 400, response.json)
                self.assertEqual(self.contagens(), before)

    def test_rollback_apos_falha_real_durante_flush(self):
        before = self.contagens()
        def falhar(mapper, connection, target):
            # A atividade e a questão já foram inseridas na transação.
            self.assertEqual(connection.scalar(sa.select(sa.func.count()).select_from(Atividade)), before[0] + 1)
            raise IntegrityError('falha controlada na alternativa', {}, Exception('erro de integridade'))
        sa.event.listen(AtividadeAlternativa, 'before_insert', falhar)
        try:
            response = self.client.post('/api/atividades', json=self.payload(), headers=self.headers('gestor'))
            self.assertEqual(response.status_code, 409)
            self.assertEqual(self.contagens(), before)
        finally:
            sa.event.remove(AtividadeAlternativa, 'before_insert', falhar)
        self.assertEqual(self.client.post('/api/atividades', json=self.payload(), headers=self.headers('gestor')).status_code, 201)

    def test_inativo_ou_inexistente_nao_acessa(self):
        user = db.session.get(User, self.ids['gestor'])
        user.ativo = False
        db.session.commit()
        try:
            self.assertEqual(self.client.get('/api/atividades', headers=self.headers('gestor')).status_code, 401)
        finally:
            user.ativo = True
            db.session.commit()
        for identidade in ('999999', 'abc', '-1', str(2**100)):
            token = create_access_token(identity=identidade)
            self.assertEqual(self.client.get('/api/atividades', headers={'Authorization': 'Bearer ' + token}).status_code, 401)

    def test_rotas_filtros_e_documentacao(self):
        for route in ('/api/atividades', '/api/atividades/1'):
            self.assertEqual(self.client.get(route).status_code, 401)
        self.assertEqual(self.client.post('/api/atividades', json=self.payload()).status_code, 401)
        self.assertEqual(self.client.patch('/api/usuarios/1/papel', json={'papel': 'admin'}).status_code, 401)
        self.assertEqual(self.client.get('/api/atividades/999999', headers=self.headers('usuario')).status_code, 404)
        self.assertEqual(self.client.get('/api/atividades?competencia_id=999999', headers=self.headers('usuario')).json, [])
        for filtro in ('competencia_id=abc', 'dificuldade=0', 'habilidade_id=1.5'):
            self.assertEqual(self.client.get('/api/atividades?'+filtro, headers=self.headers('usuario')).status_code, 400)
        spec = self.client.get('/apispec_1.json')
        self.assertEqual(spec.status_code, 200)
        for path, methods in {'/api/atividades': ('get', 'post'), '/api/atividades/{atividade_id}': ('get',),
                              '/api/usuarios/{usuario_id}/papel': ('patch',)}.items():
            for method in methods:
                operation = spec.json['paths'][path][method]
                self.assertEqual(operation['security'], [{'BearerAuth': []}])
                self.assertIn('403', operation['responses'])

    def test_migracao_de_banco_sem_papeis(self):
        sql = (Path(__file__).resolve().parents[1] / 'db/migrations/001_perfis_usuario.sql').read_text()
        before = db.session.scalar(db.select(sa.func.count()).select_from(User))
        savepoint = db.session.begin_nested()
        try:
            db.session.execute(sa.text('ALTER TABLE capacitacao.usuario DROP COLUMN papel'))
            for _ in range(2):
                db.session.execute(sa.text(sql))
            self.assertEqual(db.session.scalar(sa.text("SELECT count(*) FROM capacitacao.usuario WHERE papel = 'usuario'")), before)
            self.assertEqual(db.session.scalar(sa.text('SELECT count(*) FROM capacitacao.usuario')), before)
        finally:
            savepoint.rollback()
            db.session.expire_all()

    def test_cli_e_migracao_idempotente(self):
        response = self.app.test_cli_runner().invoke(args=['definir-perfil', 'usuario.atividades@example.com', 'gestor'])
        self.assertEqual(response.exit_code, 0, response.output)
        self.assertEqual(db.session.get(User, self.ids['usuario']).papel, 'gestor')
        db.session.get(User, self.ids['usuario']).papel = 'usuario'
        db.session.commit()
        sql = (Path(__file__).resolve().parents[1] / 'db/migrations/001_perfis_usuario.sql').read_text()
        before = db.session.scalar(db.select(sa.func.count()).select_from(User))
        for _ in range(2):
            db.session.execute(sa.text(sql))
            db.session.commit()
        self.assertEqual(db.session.scalar(db.select(sa.func.count()).select_from(User)), before)
        with self.assertRaises(IntegrityError):
            with db.session.begin_nested():
                db.session.get(User, self.ids['usuario']).papel = 'superadmin'
                db.session.flush()
