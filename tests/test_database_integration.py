"""Testes PostgreSQL. Use uma base descartável em TEST_DATABASE_URL."""
import os
from datetime import timedelta
import unittest

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import check_password_hash
from app import create_app
from app.extensions import db
from app.models import User, Competencia, Habilidade, Atividade


@unittest.skipUnless(os.getenv('TEST_DATABASE_URL'), 'Requer PostgreSQL descartável')
class DatabaseIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': os.environ['TEST_DATABASE_URL'],
            'JWT_SECRET_KEY': 'chave-exclusiva-de-testes-com-mais-de-32-caracteres',
        })
        cls.ctx = cls.app.app_context()
        cls.ctx.push()
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.engine.dispose()
        cls.ctx.pop()

    def dados(self, email):
        return dict(nome='Pessoa Teste', email=email, senha='senha-teste',
                    ambiente='individual', tempo='ate_15_min', recursos='computador', interlocutores='sozinho')

    def test_auth(self):
        response = self.client.post('/api/auth/register', json=self.dados('  TESTE@example.com  '))
        self.assertEqual(response.status_code, 201)
        user = User.query.filter_by(email='teste@example.com').one()
        self.assertTrue(check_password_hash(user.senha_hash, 'senha-teste'))
        self.assertEqual(user.perfil.ambiente, 'individual')
        self.assertTrue(user.ativo)
        self.assertIsNone(user.ultimo_login_em)
        self.assertEqual(self.client.post('/api/auth/register', json=self.dados('Teste@example.com')).status_code, 409)
        self.assertEqual(self.client.post('/api/auth/login', json={'email': 'teste@example.com', 'senha': 'errada'}).status_code, 401)
        response = self.client.post('/api/auth/login', json={'email': ' TESTE@example.com ', 'senha': 'senha-teste'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('access_token', response.json)
        db.session.refresh(user)
        self.assertIsNotNone(user.ultimo_login_em)
        user.ativo = False
        db.session.commit()
        self.assertEqual(self.client.post('/api/auth/login', json={'email': user.email, 'senha': 'senha-teste'}).status_code, 401)

    def test_invalid_json(self):
        for route in ('register', 'login'):
            for body in (None, [], {'email': 123, 'senha': []}):
                response = self.client.post('/api/auth/'+route, json=body)
                self.assertEqual(response.status_code, 400)

    def test_models_match_database(self):
        sa.orm.configure_mappers()
        reflected = sa.MetaData(schema='capacitacao')
        reflected.reflect(db.engine)
        self.assertEqual(set(db.metadata.tables), set(reflected.tables))
        for name, table in db.metadata.tables.items():
            actual = reflected.tables[name]
            self.assertEqual(set(table.columns.keys()), set(actual.columns.keys()), name)
            for column in table.columns:
                other = actual.c[column.name]
                self.assertEqual(column.nullable, other.nullable, f'{name}.{column.name}')
                self.assertEqual(str(column.type), str(other.type))
            self.assertEqual(set(table.primary_key.columns.keys()), set(actual.primary_key.columns.keys()))
            def fks(t):
                return {(tuple(f.column_keys), tuple(e.target_fullname for e in f.elements), f.ondelete)
                        for f in t.foreign_key_constraints}
            self.assertEqual(fks(table), fks(actual), name)

    def test_catalog_and_activity_integrity(self):
        self.assertEqual(Competencia.query.count(), 10)
        self.assertEqual(Habilidade.query.count(), 46)
        self.assertEqual(len(db.session.get(Competencia, 1).habilidades), 6)
        activity = Atividade(nome='Teste', competencia_id=1, habilidade_id=1, dificuldade=4, duracao_min=15)
        db.session.add(activity)
        db.session.commit()
        self.assertEqual(activity.ambiente, 'qualquer')
        self.assertEqual(activity.nivel.ordem, 4)
        with self.assertRaises(IntegrityError):
            with db.session.begin_nested():
                db.session.add(Atividade(nome='Inconsistente', competencia_id=2, habilidade_id=1, dificuldade=1, duracao_min=15))
                db.session.flush()

    def catalog_headers(self):
        return {"Authorization": "Bearer " + create_access_token(identity="1")}

    def test_catalog_routes_require_access_token(self):
        routes = ('/api/competencias', '/api/competencias/1/habilidades', '/api/niveis')
        expired = create_access_token(identity="1", expires_delta=timedelta(seconds=-1))
        refresh = create_refresh_token(identity="1")
        for route in routes:
            with self.subTest(route=route):
                self.assertEqual(self.client.get(route).status_code, 401)
                for token, status in (("invalido", 422), (expired, 401), (refresh, 422)):
                    response = self.client.get(route, headers={"Authorization": "Bearer " + token})
                    self.assertEqual(response.status_code, status)
        # A autenticação também ocorre antes de procurar a competência.
        self.assertEqual(self.client.get('/api/competencias/999999/habilidades').status_code, 401)

    def test_catalog_responses(self):
        headers = self.catalog_headers()
        response = self.client.get('/api/competencias', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 10)
        self.assertEqual([c['id'] for c in response.json], list(range(1, 11)))
        self.assertEqual(set(response.json[0]), {'id', 'nome', 'descricao'})
        response = self.client.get('/api/competencias/1/habilidades', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 6)
        self.assertEqual([h['ordem'] for h in response.json], list(range(1, 7)))
        self.assertTrue(all(h['competencia_id'] == 1 for h in response.json))
        self.assertEqual(set(response.json[0]), {'id', 'competencia_id', 'nome', 'descricao', 'ordem'})
        response = self.client.get('/api/niveis', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([n['nome'] for n in response.json], ['Iniciante', 'Básico', 'Intermediário', 'Avançado'])
        self.assertEqual([n['ordem'] for n in response.json], [1, 2, 3, 4])
        self.assertEqual([n['pontuacao_minima'] for n in response.json], [0, 25.01, 50.01, 75.01])
        self.assertEqual([n['pontuacao_maxima'] for n in response.json], [25, 50, 75, 100])
        self.assertTrue(all(isinstance(n['pontuacao_minima'], (int, float)) for n in response.json))

    def test_habilidades_empty_missing_and_order(self):
        headers = self.catalog_headers()
        response = self.client.get('/api/competencias/999999/habilidades', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json, {'error': 'Competência não encontrada.'})
        try:
            competencia = Competencia(nome='Competência temporária')
            db.session.add(competencia)
            db.session.flush()
            route = f'/api/competencias/{competencia.id}/habilidades'
            response = self.client.get(route, headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, [])
            db.session.add_all([
                Habilidade(competencia_id=competencia.id, nome='Segunda', ordem=2),
                Habilidade(competencia_id=competencia.id, nome='Primeira', ordem=1),
            ])
            db.session.flush()
            response = self.client.get(route, headers=headers)
            self.assertEqual([h['nome'] for h in response.json], ['Primeira', 'Segunda'])
            self.assertIsNone(response.json[0]['descricao'])
        finally:
            db.session.rollback()

    def test_catalog_swagger(self):
        response = self.client.get('/apispec_1.json')
        self.assertEqual(response.status_code, 200)
        spec = response.json
        self.assertEqual(spec['securityDefinitions']['BearerAuth']['name'], 'Authorization')
        for route in ('/api/competencias', '/api/competencias/{competencia_id}/habilidades', '/api/niveis'):
            operation = spec['paths'][route]['get']
            self.assertEqual(operation['security'], [{'BearerAuth': []}])
            self.assertEqual(operation['responses']['200']['schema']['type'], 'array')
            self.assertIn('401', operation['responses'])
            self.assertIn('422', operation['responses'])
        self.assertIn('404', spec['paths']['/api/competencias/{competencia_id}/habilidades']['get']['responses'])
        self.assertEqual(self.client.get('/dev').status_code, 200)

    def test_profile_history_trigger(self):
        self.client.post('/api/auth/register', json=self.dados('historico@example.com'))
        user = User.query.filter_by(email='historico@example.com').one()
        user.perfil.ambiente = 'em_equipe'
        db.session.commit()
        self.assertEqual(len(user.historicos_perfil), 1)
        self.assertEqual(user.historicos_perfil[0].ambiente, 'individual')
        user.perfil.ambiente = 'em_equipe'
        db.session.commit()
        db.session.expire(user, ['historicos_perfil'])
        self.assertEqual(len(user.historicos_perfil), 1)


if __name__ == '__main__':
    unittest.main()
