# Banco e modelos

A aplicação usa explicitamente o schema `capacitacao` nos 26 modelos SQLAlchemy.
`db/init.sql` é a fonte da instalação inicial, incluindo índices, dados de referência
 e o trigger de histórico. Não use `db.create_all()` para substituir a instalação:
 o trigger e os dados de referência são definidos no SQL.

## Instalação nova

O Docker Compose monta `db/init.sql` na inicialização do PostgreSQL. Isso só é
executado automaticamente quando o volume de dados está vazio.

## Atualização do banco local existente

Com o PostgreSQL em execução e as variáveis `POSTGRES_*` no `.env`:

```bash
venv/bin/python scripts/atualizar_banco_local.py
```

O script aceita apenas host local, instala o SQL em uma transação e copia as
contas de `public.usuario`, mantendo IDs e hashes de senha. Normaliza os emails
e copia os perfis antigos, tanto de colunas em `usuario` como de `perfil_usuario`.
Uma falha reverte toda a instalação. Se `capacitacao` já existir, não faz alterações;
essa verificação não substitui migrações futuras.

As tabelas antigas permanecem intactas em `public`. Conteúdo antigo de atividades,
recomendações e execuções não é convertido: a nova estrutura exige habilidade,
nível e avaliação de origem. Esse conteúdo precisa de um mapeamento específico
antes de ser transferido. O catálogo novo vem da carga inicial do SQL.

A autenticação usa `senha_hash`, recusa contas inativas e registra
`ultimo_login_em` em um login válido. Cadastro e login normalizam o email.
Os contratos de `/api/auth/register` e `/api/auth/login` continuam recebendo `senha`.

## Verificação

```bash
venv/bin/python test_models.py
venv/bin/python scripts/testar_banco_local.py
```

O segundo comando exige permissão para criar uma base no PostgreSQL local.
Ele cria uma base descartável, executa `init.sql`, roda os testes de integração
e remove a base ao terminar. As tabelas do banco da aplicação não são usadas.
Também é possível executar os testes contra uma base descartável já instalada:

```bash
TEST_DATABASE_URL='postgresql+psycopg2://usuario:senha@localhost/base_testes' venv/bin/python -m unittest discover -s tests -v
```
