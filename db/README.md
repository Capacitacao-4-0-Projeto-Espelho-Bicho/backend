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
Uma falha reverte toda a instalação. Se `capacitacao` já existir, aplica as migrações incrementais de
`db/migrations` na mesma transação, preservando os dados. As migrações atuais
são idempotentes e podem ser executadas novamente.

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

## Perfis e atividades

As contas novas e existentes recebem o papel `usuario`. O cadastro público não
permite escolher privilégios. O campo `papel` aceita `usuario`, `gestor` e `admin`.

| Operação | usuario | gestor | admin |
|---|---|---|---|
| Listar e consultar atividades | Sim | Sim | Sim |
| Ver pontuações e justificativas das alternativas | Não | Sim | Sim |
| Cadastrar atividades completas | Não | Sim | Sim |
| Alterar papéis de usuários pela API | Não | Não | Sim |

Depois de aplicar a atualização do banco, use o terminal do servidor para
promover uma conta existente e estabelecer o primeiro administrador:

```bash
venv/bin/flask --app run definir-perfil seu-email@example.com admin
```

O comando exige acesso ao ambiente do servidor e usa a conexão da aplicação
(`DATABASE_URL`, quando definida, tem prioridade). Nenhuma conta é promovida
automaticamente. Para testes locais, confira a configuração antes de executar.

Com um token de admin, também é possível usar
`PATCH /api/usuarios/<id>/papel` com `{"papel": "gestor"}`. As permissões destas
rotas são lidas do banco a cada chamada, sem confiar em papéis antigos no token.

As rotas `POST /api/atividades`, `GET /api/atividades` e
`GET /api/atividades/<id>` estão documentadas no Swagger em `/dev`, incluindo
um exemplo completo para criação. A listagem aceita os filtros opcionais
`competencia_id`, `habilidade_id` e `dificuldade`.

O cadastro exige ao menos uma questão e duas alternativas por questão,
pontuação explícita entre 0 e 99999.99 com até duas casas decimais, e ordens
positivas e únicas em cada conjunto. A habilidade deve pertencer à competência,
e a dificuldade deve existir no catálogo de níveis. O contexto omitido usa
`qualquer`. Qualquer falha reverte atividade, questões e alternativas juntas.

## Questões de nivelamento

`POST /api/tarefas` permite que gestor e admin cadastrem uma questão de
nivelamento e suas alternativas na mesma transação. A rota exige JWT e está
no grupo **Nivelamento** do Swagger `/dev`, com exemplo completo.

Campos obrigatórios: `habilidade_id`, `nivel_id`, `enunciado`, `ordem` e
`alternativas`. Cada alternativa exige `texto`, `ordem` e `pontuacao`.
A competência é determinada pela habilidade; habilidade e nível devem existir.
São aceitas de duas a cinco alternativas, com ordens únicas entre 1 e 5,
pontuações de 0 a 99999.99 e até duas casas decimais. A ordem da questão é
positiva; não é exigida exclusividade entre questões, pois o schema não define
esse agrupamento. `instrucoes` e `justificativa` são opcionais;
`tempo_estimado_min` é positivo e usa 15 quando omitido.

A resposta `201` inclui a questão, as alternativas ordenadas e seus IDs,
pontuações e justificativas, para conferência editorial. Dados inválidos retornam
`400`; conflito de integridade retorna `409`. Ambos preservam a atomicidade:
nenhuma parte da questão fica gravada. Usuários comuns recebem `403`.

Essa rota alimenta `tarefa`/`alternativa`, usadas no nivelamento, e não
`atividade`/`atividade_questao`, usadas nas atividades de desenvolvimento.
Não exige migração: as tabelas já fazem parte de `init.sql`. A execução da
avaliação pelo usuário e o cálculo do resultado ainda não estão implementados.

## Competências escolhidas e início de nivelamento

Todas as rotas abaixo exigem JWT e uma conta ativa (`usuario`, `gestor` ou
`admin`), e operam exclusivamente sobre o usuário identificado pelo token.
Estão documentadas no grupo **Meu nivelamento** do Swagger `/dev`.

1. `PUT /api/usuarios/me/competencias` recebe `{"competencia_ids": [5, 10]}`.
   A lista representa a seleção completa: IDs inexistentes, inválidos ou
   repetidos retornam `400` sem mudar a seleção. `[]` desativa todas as escolhas.
   Itens removidos ficam inativos; avaliações e resultados anteriores permanecem.
2. `GET /api/usuarios/me/competencias` lista as escolhas ativas com nome,
   descrição e `nivelamento`: `status`, `avaliacao_id` e `nivel`.
   O status é `pendente`, `em_andamento` ou `concluida`. Sem avaliação, ou
   após cancelamento, `avaliacao_id` e `nivel` são nulos. Uma avaliação concluída
   pode retornar o nível obtido em `nivel` (`id` e `nome`).
3. `POST /api/usuarios/me/competencias/<id>/nivelamento` não exige corpo.
   Inicia uma avaliação (`201`) ou retoma a aberta (`200`), retornando
   `avaliacao_id`, `competencia_id`, `status` e `questoes` com alternativas.
   Pontuações, justificativas e nível atribuído à questão não são expostos.

A primeira tentativa inclui todas as questões cadastradas das habilidades da
competência, em todos os níveis. São ordenadas pela habilidade e depois pela
questão, com os IDs como desempate; alternativas vêm por ordem. O conjunto
inicial e o máximo de pontos por questão são registrados em `avaliacao_tarefa`.
Questões novas não são acrescentadas à tentativa quando ela é retomada.

Competência não selecionada ou inativa retorna `404`. Sem questões completas,
com máximo total zero, com nivelamento já concluído ou com reavaliação em
andamento, retorna `409`. Cada questão precisa de pelo menos duas alternativas.
O máximo de cada questão é a maior pontuação de suas alternativas; o total
precisa ser positivo. Qualquer falha reverte a criação completa da avaliação.
Seleção e início usam o mesmo bloqueio por usuário para coordenar chamadas
concorrentes, além do índice que impede duas avaliações abertas por competência.

As tabelas já existem; esta entrega não exige migração. O envio de respostas,
a conclusão, o cálculo do nível e a reavaliação ficam para a próxima etapa.

## Roteiro manual por perfil

Veja [os fluxos completos de usuário, gestor e admin](../docs/fluxos-testes.md),
com preparação, exemplos de JSON, permissões, isolamento e resultados esperados.
