"""Instala o schema novo e preserva contas locais; não altera o schema public."""
from pathlib import Path
import os
import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def conectar():
    load_dotenv(ROOT / '.env')
    host = os.getenv('POSTGRES_HOST', 'localhost')
    if host not in ('localhost', '127.0.0.1', '::1'):
        raise RuntimeError('Este script aceita apenas um PostgreSQL local.')
    return psycopg2.connect(host=host, port=os.getenv('POSTGRES_PORT', '5432'),
                            dbname=os.getenv('POSTGRES_DB'), user=os.getenv('POSTGRES_USER'),
                            password=os.getenv('POSTGRES_PASSWORD'))


def atualizar(conn):
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(743912)")
            cur.execute("SELECT to_regnamespace('capacitacao')")
            if cur.fetchone()[0] is not None:
                print('Schema capacitacao já existe; nenhuma alteração aplicada.')
                return
            sql = (ROOT / 'db/init.sql').read_text()
            # A transação é controlada por este script, incluindo a cópia das contas.
            sql = sql.replace('BEGIN;', '', 1).rsplit('COMMIT;', 1)[0]
            cur.execute(sql)
            cur.execute("SELECT to_regclass('public.usuario')")
            if cur.fetchone()[0] is not None:
                cur.execute("""INSERT INTO capacitacao.usuario
                    (id, nome, email, senha_hash, data_cadastro)
                    SELECT id, nome, lower(trim(email)), senha, data_cadastro
                    FROM public.usuario""")
                cur.execute("""SELECT column_name FROM information_schema.columns
                    WHERE table_schema='public' AND table_name='usuario'""")
                cols = {row[0] for row in cur.fetchall()}
                if {'ambiente', 'tempo', 'recursos', 'interlocutores'} <= cols:
                    cur.execute("""INSERT INTO capacitacao.perfil_usuario
                        (usuario_id, ambiente, tempo, recursos, interlocutores)
                        SELECT id, ambiente, tempo, recursos, interlocutores FROM public.usuario
                        WHERE ambiente IS NOT NULL AND tempo IS NOT NULL
                          AND recursos IS NOT NULL AND interlocutores IS NOT NULL""")
                cur.execute("SELECT to_regclass('public.perfil_usuario')")
                if cur.fetchone()[0] is not None:
                    cur.execute("""INSERT INTO capacitacao.perfil_usuario
                        (usuario_id, ambiente, tempo, recursos, interlocutores, origem_atualizacao, atualizado_em)
                        SELECT usuario_id, ambiente, tempo, recursos, interlocutores,
                               origem_atualizacao, COALESCE(atualizado_em, CURRENT_TIMESTAMP)
                        FROM public.perfil_usuario ON CONFLICT (usuario_id) DO NOTHING""")
                cur.execute("""SELECT setval(pg_get_serial_sequence('capacitacao.usuario','id'),
                    COALESCE(MAX(id),1), COUNT(*)>0) FROM capacitacao.usuario""")
    print('Schema instalado e contas preservadas. Tabelas antigas mantidas em public.')


if __name__ == '__main__':
    conn = conectar()
    try:
        atualizar(conn)
    finally:
        conn.close()
