"""Testes PostgreSQL. Use uma base descartável em TEST_DATABASE_URL."""
import os
import unittest

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
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
