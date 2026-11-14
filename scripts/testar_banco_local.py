"""Cria e remove uma base descartável no PostgreSQL local para testes."""
import os
import sys
import uuid
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.atualizar_banco_local import conectar, atualizar
from psycopg2 import sql
import psycopg2
from sqlalchemy.engine import URL

admin = conectar()
admin.autocommit = True
params = admin.get_dsn_parameters()
name = 'backend_test_' + uuid.uuid4().hex[:12]
with admin.cursor() as c:
    c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
try:
    # psycopg2 DSN does not expose the password; get it from the loaded environment.
    url = URL.create('postgresql+psycopg2', username=params['user'], password=os.getenv('POSTGRES_PASSWORD'), host=params['host'], port=int(params['port']), database=name)
    os.environ['TEST_DATABASE_URL'] = url.render_as_string(hide_password=False)
    conn = psycopg2.connect(host=params['host'], port=params['port'], user=params['user'], password=os.getenv('POSTGRES_PASSWORD'), dbname=name)
    with conn.cursor() as c:
        c.execute((ROOT / 'db/init.sql').read_text())
    conn.close()
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
finally:
    with admin.cursor() as c:
        c.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
    admin.close()
sys.exit(not result.wasSuccessful())
