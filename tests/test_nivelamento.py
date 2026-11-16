"""Seleção pessoal e início/retomada de avaliações de nivelamento."""
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from flask_jwt_extended import create_access_token
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import (
    User, Competencia, Habilidade, Tarefa, Alternativa, UsuarioCompetencia,
    AvaliacaoUsuario, AvaliacaoTarefa,
)


@unittest.skipUnless(os.getenv('TEST_DATABASE_URL'), 'Requer PostgreSQL descartável')
class NivelamentoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': os.environ['TEST_DATABASE_URL'],
                             'JWT_SECRET_KEY': 'chave-exclusiva-de-testes-com-mais-de-32-caracteres'})

    def setUp(self):
        self.ctx = self.app.app_context(); self.ctx.push()
        self.client = self.app.test_client()
        self.users = []
        for indice in range(2):
            user = User(nome='Teste', email=f'{self._testMethodName}.{indice}@nivelamento.com',
                        senha_hash=generate_password_hash('teste'))
            db.session.add(user); db.session.flush(); self.users.append(user.id)
        # Catálogos próprios para não depender das questões criadas por outros testes.
        self.competencias = []
        self.habilidades = []
        for i in range(2):
            c = Competencia(nome=f'{self._testMethodName}.{i}')
            db.session.add(c); db.session.flush(); self.competencias.append(c.id)
            h = Habilidade(competencia_id=c.id, nome='Habilidade', ordem=1)
            db.session.add(h); db.session.flush(); self.habilidades.append(h.id)
        db.session.commit()

    def tearDown(self):
        db.session.remove(); self.ctx.pop()

    def headers(self, indice=0):
        return {'Authorization': 'Bearer '+create_access_token(identity=str(self.users[indice]))}

    def selecionar(self, ids, indice=0):
        return self.client.put('/api/usuarios/me/competencias', json={'competencia_ids': ids}, headers=self.headers(indice))

    def listar(self, indice=0):
        return self.client.get('/api/usuarios/me/competencias', headers=self.headers(indice))

    def iniciar(self, competencia=None, indice=0):
        cid = self.competencias[0] if competencia is None else competencia
        return self.client.post(f'/api/usuarios/me/competencias/{cid}/nivelamento', headers=self.headers(indice))

    def tarefa(self, indice=0, ordem=1, pontos=3):
        t = Tarefa(habilidade_id=self.habilidades[indice], nivel_id=1, enunciado='Questão', ordem=ordem)
        t.alternativas = [Alternativa(texto='Segunda', ordem=2, pontuacao=pontos, justificativa='Privado'),
                          Alternativa(texto='Primeira', ordem=1, pontuacao=0)]
        db.session.add(t); db.session.commit()
        return t.id

    def test_selecao_consulta_idempotencia_e_isolamento(self):
        self.assertEqual(self.listar().json, [])
        response = self.selecionar(self.competencias[::-1])
        self.assertEqual(response.status_code, 200)
        self.assertEqual([c['competencia_id'] for c in response.json], self.competencias)
        self.assertTrue(all(c['nivelamento'] == {'status':'pendente','avaliacao_id':None,'nivel':None} for c in response.json))
        original = db.session.get(UsuarioCompetencia, (self.users[0], self.competencias[0])).selecionada_em
        self.assertEqual(self.selecionar(self.competencias).status_code, 200)
        self.assertEqual(db.session.get(UsuarioCompetencia, (self.users[0], self.competencias[0])).selecionada_em, original)
        self.assertEqual(self.listar(1).json, [])
        self.assertEqual(self.iniciar(indice=1).status_code, 404)
        response = self.client.put('/api/usuarios/me/competencias', json={'competencia_ids':[], 'usuario_id':self.users[0]}, headers=self.headers(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.listar().json), 2)
        self.selecionar([])
        self.assertEqual(self.listar().json, [])
        self.assertFalse(db.session.get(UsuarioCompetencia, (self.users[0], self.competencias[0])).ativa)

    def test_selecao_invalida_preserva_estado(self):
        self.selecionar(self.competencias)
        for dados in (None, [], {}, {'competencia_ids':'1'}, {'competencia_ids':[True]},
                      {'competencia_ids':[0]}, {'competencia_ids':[2**80]},
                      {'competencia_ids':[self.competencias[0]]*2}, {'competencia_ids':[self.competencias[0],999999]}):
            response = self.client.put('/api/usuarios/me/competencias', json=dados, headers=self.headers())
            self.assertEqual(response.status_code, 400, response.json)
            self.assertEqual(len(self.listar().json), 2)

    def test_inicia_retorna_e_preserva_conjunto_da_tentativa(self):
        self.selecionar(self.competencias)
        segunda = self.tarefa(ordem=2); primeira = self.tarefa(ordem=1, pontos=2)
        outra = self.tarefa(indice=1)
        response = self.iniciar()
        self.assertEqual(response.status_code, 201, response.json)
        dados = response.json
        self.assertEqual([q['id'] for q in dados['questoes']], [primeira, segunda])
        for q in dados['questoes']:
            self.assertNotIn('nivel_id', q)
            for a in q['alternativas']:
                self.assertEqual(set(a), {'id','texto','ordem'})
        av = db.session.get(AvaliacaoUsuario, dados['avaliacao_id'])
        self.assertEqual(float(av.pontuacao_maxima), 5)
        links = db.session.scalars(db.select(AvaliacaoTarefa).where(AvaliacaoTarefa.avaliacao_id==av.id)).all()
        self.assertEqual(sorted(float(l.pontuacao_maxima) for l in links), [2,3])
        self.tarefa(ordem=3)
        retomada = self.iniciar()
        self.assertEqual(retomada.status_code, 200)
        self.assertEqual(retomada.json, dados)
        outra_av = self.iniciar(self.competencias[1])
        self.assertEqual(outra_av.status_code, 201)
        self.assertNotEqual(outra_av.json['avaliacao_id'], dados['avaliacao_id'])
        self.assertEqual([q['id'] for q in outra_av.json['questoes']], [outra])
        self.assertEqual([c['nivelamento']['status'] for c in self.listar().json], ['em_andamento']*2)
        self.selecionar([self.competencias[1]])
        self.assertEqual(self.iniciar().status_code, 404)
        self.assertIsNotNone(db.session.get(AvaliacaoUsuario, av.id))
        self.selecionar(self.competencias)
        self.assertEqual(self.iniciar().json['avaliacao_id'], av.id)

    def test_sem_questoes_incompletas_ou_maximo_zero(self):
        self.selecionar(self.competencias)
        self.assertEqual(self.iniciar().status_code, 409)
        tid = self.tarefa(pontos=0)
        self.assertEqual(self.iniciar().status_code, 409)
        t = db.session.get(Tarefa, tid)
        db.session.delete(t.alternativas[0]); db.session.commit()
        self.assertEqual(self.iniciar().status_code, 409)
        count = db.session.scalar(db.select(sa.func.count()).select_from(AvaliacaoUsuario).where(AvaliacaoUsuario.usuario_id==self.users[0]))
        self.assertEqual(count, 0)
        self.assertEqual(self.iniciar(999999).status_code, 404)

    def test_concluida_e_cancelada(self):
        self.selecionar(self.competencias)
        self.tarefa()
        response = self.iniciar()
        av = db.session.get(AvaliacaoUsuario, response.json['avaliacao_id'])
        av.status = 'cancelada'; db.session.commit()
        self.assertEqual(self.listar().json[0]['nivelamento']['status'], 'pendente')
        nova = self.iniciar(); self.assertEqual(nova.status_code, 201)
        self.assertNotEqual(nova.json['avaliacao_id'], av.id)
        av = db.session.get(AvaliacaoUsuario, nova.json['avaliacao_id'])
        av.status = 'concluida'; av.nivel_id = 2; db.session.commit()
        resultado = self.listar().json[0]['nivelamento']
        self.assertEqual(resultado['status'], 'concluida')
        self.assertEqual(resultado['nivel'], {'id':2, 'nome':'Básico'})
        self.assertEqual(self.iniciar().status_code, 409)

    def test_rollback_durante_criacao(self):
        self.selecionar(self.competencias); self.tarefa()
        def falhar(mapper, connection, target):
            raise IntegrityError('Falha no vínculo', {}, Exception('integridade'))
        sa.event.listen(AvaliacaoTarefa, 'before_insert', falhar)
        try:
            self.assertEqual(self.iniciar().status_code, 409)
            self.assertEqual(db.session.scalar(db.select(sa.func.count()).select_from(AvaliacaoUsuario).where(AvaliacaoUsuario.usuario_id==self.users[0])), 0)
        finally:
            sa.event.remove(AvaliacaoTarefa, 'before_insert', falhar)
        self.assertEqual(self.iniciar().status_code, 201)

    def test_inicios_concorrentes_retomam_mesma_avaliacao(self):
        self.selecionar(self.competencias); self.tarefa()
        headers = self.headers(); url = f'/api/usuarios/me/competencias/{self.competencias[0]}/nivelamento'
        barrier = Barrier(2)
        def iniciar():
            with self.app.test_client() as client:
                barrier.wait(timeout=10)
                response = client.post(url, headers=headers)
                return response.status_code, response.json
        # Libera qualquer transação de leitura antes das chamadas paralelas.
        db.session.remove()
        with ThreadPoolExecutor(max_workers=2) as pool:
            resultados = list(pool.map(lambda _: iniciar(), range(2)))
        self.assertEqual(sorted(r[0] for r in resultados), [200,201])
        self.assertEqual(resultados[0][1]['avaliacao_id'], resultados[1][1]['avaliacao_id'])

    def test_jwt_documentacao(self):
        routes = {'/api/usuarios/me/competencias':('get','put'),
                  f'/api/usuarios/me/competencias/{self.competencias[0]}/nivelamento':('post',)}
        for route, methods in routes.items():
            for method in methods:
                self.assertEqual(self.client.open(route, method=method).status_code, 401)
        spec = self.client.get('/apispec_1.json')
        self.assertEqual(spec.status_code, 200)
        for route, methods in {'/api/usuarios/me/competencias':('get','put'),
                               '/api/usuarios/me/competencias/{competencia_id}/nivelamento':('post',)}.items():
            for method in methods:
                self.assertEqual(spec.json['paths'][route][method]['security'], [{'BearerAuth':[]}])
