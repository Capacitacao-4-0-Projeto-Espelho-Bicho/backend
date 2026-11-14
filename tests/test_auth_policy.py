"""Proteção centralizada, sem conexão com o banco."""
from datetime import timedelta
import unittest

from flask_jwt_extended import create_access_token, create_refresh_token

from app import create_app


class AuthPolicyTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite://',
            'JWT_SECRET_KEY': 'chave-exclusiva-de-testes-com-mais-de-32-caracteres',
        })

        # Sem @jwt_required: a política precisa proteger inclusive rotas futuras.
        @self.app.route('/api/teste-politica', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
        def teste_politica():
            return {'ok': True}

        self.client = self.app.test_client()

    def token(self, tipo='acesso'):
        with self.app.app_context():
            if tipo == 'expirado':
                return create_access_token(identity='1', expires_delta=timedelta(seconds=-1))
            if tipo == 'refresh':
                return create_refresh_token(identity='1')
            return create_access_token(identity='1')

    def test_nova_rota_exige_jwt_em_todos_os_metodos(self):
        headers = {'Authorization': 'Bearer ' + self.token()}
        for method in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD'):
            with self.subTest(method=method):
                self.assertEqual(self.client.open('/api/teste-politica', method=method).status_code, 401)
                self.assertEqual(self.client.open('/api/teste-politica', method=method, headers=headers).status_code, 200)

    def test_rejeita_tokens_invalidos(self):
        for token, status in (('invalido', 422), (self.token('expirado'), 401), (self.token('refresh'), 422)):
            with self.subTest(status=status):
                response = self.client.get('/api/teste-politica', headers={'Authorization': 'Bearer ' + token})
                self.assertEqual(response.status_code, status)

    def test_excecoes_publicas(self):
        # Corpos vazios exercitam a validação das rotas, sem acessar o banco.
        for route in ('/api/auth/login', '/api/auth/register'):
            self.assertEqual(self.client.post(route, json={}).status_code, 400)
        self.assertEqual(self.client.get('/dev').status_code, 200)
        self.assertEqual(self.client.get('/apispec_1.json').status_code, 200)
        self.assertEqual(self.client.options('/api/teste-politica').status_code, 200)

    def test_demais_rotas_auth_continuam_protegidas(self):
        self.assertEqual(self.client.get('/api/auth/outra-rota').status_code, 401)
        self.assertEqual(self.client.get('/api').status_code, 401)
