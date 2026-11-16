# Roteiro de testes por perfil

Este roteiro cobre todas as operações implementadas, usando o Swagger em
[http://localhost:5000/dev](http://localhost:5000/dev). Use o banco local de
desenvolvimento. Cadastros, conteúdos e seleções feitos manualmente ficam salvos.
Não é necessário executar SQL manualmente.

## 1. Preparação

Na raiz do repositório, com o `.env` apontando para o PostgreSQL local:

```bash
source venv/bin/activate
python -m pip install -r requirements.txt
docker compose up -d db
python scripts/atualizar_banco_local.py
python run.py
```

Confira o `JWT_SECRET_KEY`. Se `DATABASE_URL` estiver definida, ela tem prioridade
sobre `POSTGRES_*` na API e no comando de definição de perfil; o atualizador local
usa `POSTGRES_*`. Ambos devem apontar para o banco que você quer testar.

### Criar contas dedicadas

No Swagger, execute `POST /api/auth/register` com este corpo:

```json
{
  "nome": "QA Usuário",
  "email": "qa.usuario@example.com",
  "senha": "SenhaLocal123!",
  "ambiente": "individual",
  "tempo": "ate_15_min",
  "recursos": "computador",
  "interlocutores": "sozinho"
}
```

Repita mudando nome e email para criar as outras contas:

| Conta | Email | Papel final |
|---|---|---|
| Usuário principal | `qa.usuario@example.com` | `usuario` |
| Outro usuário, para isolamento | `qa.outro@example.com` | `usuario` |
| Gestor | `qa.gestor@example.com` | `gestor` |
| Administrador | `qa.admin@example.com` | `admin` |

Use a mesma senha de exemplo somente nestas contas locais. Cada cadastro deve
retornar **201**. Anote o `user.id` retornado para cada conta. Se houver **409**,
a conta já existe; use a senha conhecida ou escolha outro email.

Todas nascem como `usuario`. Em outro terminal, crie o primeiro admin:

```bash
source venv/bin/activate
flask --app run definir-perfil qa.admin@example.com admin
```

Faça login como `qa.admin@example.com` em `POST /api/auth/login`:

```json
{
  "email": "qa.admin@example.com",
  "senha": "SenhaLocal123!"
}
```

Resultado: **200**, com `access_token`. Em **Authorize**, informe:

```text
Bearer COLE_O_ACCESS_TOKEN_AQUI
```

Use `PATCH /api/usuarios/{usuario_id}/papel`, preenchendo o ID real do gestor:

```json
{"papel": "gestor"}
```

Esperado: **200**, com o ID e o novo papel. Agora as contas estão prontas.

### Como trocar de perfil durante os testes

Faça login com a conta desejada, copie o token, abra **Authorize**, remova a
autorização anterior e informe `Bearer NOVO_TOKEN`. Não basta fazer login: é
necessário trocar o token em **Authorize**. Anote qual conta está em uso.

## 2. Mapa de permissões

Login e cadastro são públicos. As demais operações exigem token de acesso.
O papel da API chama-se `usuario`, e não `user`.

| Operação | usuario | gestor | admin |
|---|---|---|---|
| `GET /api/competencias` | 200 | 200 | 200 |
| `GET /api/competencias/{competencia_id}/habilidades` | 200 | 200 | 200 |
| `GET /api/niveis` | 200 | 200 | 200 |
| `GET /api/atividades` | 200 | 200 | 200 |
| `GET /api/atividades/{atividade_id}` | 200, sem pontuações/justificativas | 200, conteúdo completo | 200, conteúdo completo |
| `POST /api/atividades` | 403 | 201 | 201 |
| `POST /api/tarefas` | 403 | 201 | 201 |
| `PUT /api/usuarios/me/competencias` | 200, próprias | 200, próprias | 200, próprias |
| `GET /api/usuarios/me/competencias` | 200, próprias | 200, próprias | 200, próprias |
| `POST /api/usuarios/me/competencias/{competencia_id}/nivelamento` | 201 ou 200, próprio | 201 ou 200, próprio | 201 ou 200, próprio |
| `PATCH /api/usuarios/{usuario_id}/papel` | 403 | 403 | 200 |

Os sucessos da tabela pressupõem IDs existentes e dados válidos. Admin também
usa `/me` para suas próprias escolhas; esse caminho não consulta outro usuário.

## 3. Conteúdo compartilhado: preparar como admin

Antes dos fluxos pessoais, cadastre questões para duas competências e uma
atividade para que todas as contas tenham conteúdo para consultar.

### A. Conferir o catálogo

- [ ] `GET /api/competencias` → **200**, lista de competências.
- [ ] `GET /api/competencias/1/habilidades` → **200**, habilidades por ordem.
- [ ] `GET /api/niveis` → **200**, quatro níveis ordenados e faixas numéricas.

No catálogo inicial, habilidade `1` pertence à competência `1`, e habilidade `7`
pertence à competência `2`. Se o catálogo foi alterado, substitua os IDs nos
exemplos após consultar as habilidades de cada competência.

### B. Criar uma questão para a competência 1

`POST /api/tarefas`:

```json
{
  "habilidade_id": 1,
  "nivel_id": 1,
  "enunciado": "QA: como você analisa um processo?",
  "instrucoes": "Escolha a opção mais próxima da sua prática.",
  "ordem": 1,
  "tempo_estimado_min": 10,
  "alternativas": [
    {"texto": "Observo só o resultado.", "ordem": 1, "pontuacao": 0},
    {
      "texto": "Identifico etapas e relações.",
      "ordem": 2,
      "pontuacao": 3,
      "justificativa": "Considera o processo e seu contexto."
    }
  ]
}
```

- [ ] Retorna **201**, com ID da questão e IDs das alternativas.
- [ ] Resposta editorial inclui pontuações e justificativas.

Repita com `habilidade_id: 7` e enunciado `QA: como você aprende algo novo?`,
para preparar a competência `2`. Esperado: **201**.

### C. Criar uma atividade de desenvolvimento

`POST /api/atividades`:

```json
{
  "nome": "QA: análise de processos",
  "descricao": "Atividade de teste manual.",
  "competencia_id": 1,
  "habilidade_id": 1,
  "dificuldade": 1,
  "duracao_min": 15,
  "questoes": [
    {
      "enunciado": "Qual abordagem considera o contexto?",
      "ordem": 1,
      "alternativas": [
        {"texto": "Analisar etapas e relações.", "ordem": 1, "pontuacao": 3, "justificativa": "Visão do processo."},
        {"texto": "Analisar apenas o resultado.", "ordem": 2, "pontuacao": 0}
      ]
    }
  ]
}
```

- [ ] Retorna **201**, com atividade, questões e alternativas.
- [ ] Anote o ID como `ID_ATIVIDADE`; substitua esse marcador nos testes abaixo.
- [ ] Campos de contexto omitidos retornam `qualquer`.

Questões em `/tarefas` alimentam o nivelamento. Questões dentro de `/atividades`
alimentam as atividades de desenvolvimento; criar uma não substitui a outra.

## 4. Fluxo de usuário comum

Autorize com o token de `qa.usuario@example.com`.

### Consultar catálogo e atividades

- [ ] Execute as três consultas de catálogo da seção 3A → **200** em todas.
- [ ] `GET /api/atividades` → **200**; encontre `ID_ATIVIDADE`.
- [ ] `GET /api/atividades?competencia_id=1&habilidade_id=1&dificuldade=1`
  → **200**, somente atividades que atendam aos três filtros.
- [ ] `GET /api/atividades/ID_ATIVIDADE` → **200**, com questões e alternativas
  ordenadas. Nenhuma alternativa deve expor `pontuacao` ou `justificativa`.
- [ ] `GET /api/atividades/999999` → **404**, se esse ID não existir.

### Escolher competências e abrir as duas avaliações

- [ ] `GET /api/usuarios/me/competencias` → **200**, inicialmente `[]` nesta conta nova.
- [ ] Execute `PUT /api/usuarios/me/competencias`:

```json
{"competencia_ids": [1, 2]}
```

- [ ] Retorna **200**, duas competências com `status: pendente`,
  `avaliacao_id: null` e `nivel: null`.
- [ ] Repita o mesmo PUT → **200**, sem duplicar escolhas.
- [ ] Consulte o GET novamente → as duas escolhas continuam presentes.
- [ ] `POST /api/usuarios/me/competencias/1/nivelamento`, sem corpo → **201**.
  Anote `avaliacao_id` como `AVALIACAO_1`.
- [ ] A resposta traz questões e alternativas da competência 1, sem pontuações,
  justificativas ou `nivel_id` das questões.
- [ ] Repita o POST → **200**, mesmo `AVALIACAO_1` e mesmo conjunto de questões.
- [ ] Consulte as escolhidas → competência 1 `em_andamento`, competência 2 `pendente`.
- [ ] `POST /api/usuarios/me/competencias/2/nivelamento` → **201**, outro
  `avaliacao_id`, com as questões da competência 2.
- [ ] Consulte as escolhidas → ambas `em_andamento`, cada uma com sua avaliação.

A tentativa usa todas as questões existentes da competência, não apenas a
questão QA criada neste roteiro. O nível do usuário ainda não é calculado nesta
entrega e permanece nulo enquanto a avaliação estiver em andamento.

### Alterar a seleção sem perder a tentativa

- [ ] Envie `{"competencia_ids": [2]}` no PUT → somente a competência 2 fica ativa.
- [ ] Tente abrir a competência 1 → **404**.
- [ ] Envie `{"competencia_ids": [1, 2]}` → ambas voltam a aparecer.
- [ ] Abra a competência 1 → **200**, mesmo `AVALIACAO_1`.
- [ ] Envie `{"competencia_ids": []}` → **200**, lista vazia.
- [ ] GET das escolhidas → `[]`; abrir 1 ou 2 → **404**.
- [ ] Reative `[1, 2]` para deixar a conta pronta para continuar os testes.

### Confirmar bloqueios

- [ ] `POST /api/atividades`, com o exemplo válido → **403**.
- [ ] `POST /api/tarefas`, com o exemplo válido → **403**.
- [ ] `PATCH /api/usuarios/{ID_USUARIO}/papel` com `{"papel":"admin"}` → **403**.
- [ ] Tente iniciar uma competência existente não selecionada → **404**.

## 5. Fluxo de gestor

Autorize com o token de `qa.gestor@example.com`.

- [ ] Execute todas as consultas do catálogo → **200**.
- [ ] Liste atividades e consulte `ID_ATIVIDADE` → **200**.
- [ ] No detalhe, confira que as alternativas incluem `pontuacao` e `justificativa`.
- [ ] Cadastre uma atividade usando a seção 3C, com nome `QA: criada pelo gestor`
  → **201**. Consulte o ID retornado → **200**.
- [ ] Cadastre uma questão usando a seção 3B, com enunciado
  `QA: questão criada pelo gestor` → **201**.
- [ ] Repita o fluxo de escolhas e nivelamento da seção 4 nesta conta: pode
  selecionar, consultar, iniciar, retomar, remover e reativar suas competências.
- [ ] As avaliações do gestor têm IDs diferentes das avaliações do usuário.
- [ ] Tente alterar o papel de qualquer conta com PATCH → **403**, inclusive se
  tentar alterar o próprio papel para `admin` ou promover outra conta a `gestor`.

Cadastre o conteúdo do gestor antes de iniciar sua avaliação para que ele entre
na tentativa. Novas questões não são acrescentadas a avaliações já abertas.

## 6. Fluxo de admin

Autorize com o token de `qa.admin@example.com`.

- [ ] Execute consultas do catálogo, listagem e detalhe de atividade → **200**.
- [ ] Confira pontuações e justificativas no detalhe da atividade.
- [ ] Crie atividade e questão como nas seções 3B/3C → **201**.
- [ ] Repita seleção, consulta, início, retomada e alteração da seleção na própria
  conta → mesmos comportamentos do usuário, com avaliações próprias.

### Gerenciar permissões

Use o ID da conta `qa.outro@example.com`, mantendo o admin original ativo:

- [ ] PATCH com `{"papel":"gestor"}` → **200**.
- [ ] Autorize como `qa.outro@example.com` e crie atividade → **201**.
- [ ] Com o admin original, altere a conta para `usuario` → **200**.
- [ ] Volte ao token já emitido de `qa.outro@example.com` e tente criar atividade
  → **403**, mesmo sem fazer login novamente.
- [ ] Com o admin original, altere essa conta para `admin` → **200**.
- [ ] Com o token da conta promovida, altere o papel do gestor para `gestor`
  (mesmo papel) → **200**, confirmando acesso à administração.
- [ ] Com o admin original, restaure `qa.outro@example.com` para `usuario`.
- [ ] Papel `superadmin` → **400**, sem alterar o papel atual.
- [ ] ID inexistente, por exemplo `999999`, com papel válido → **404**.

Essas operações alteram o banco local. Não use IDs de contas reais que não fazem
parte do roteiro e mantenha a conta admin principal com acesso administrativo.

## 7. Isolamento entre contas

- [ ] Deixe `[1, 2]` selecionadas para `qa.usuario@example.com`.
- [ ] Autorize como `qa.outro@example.com` e salve `[]` nas escolhas.
- [ ] O GET de `qa.outro@example.com` retorna `[]`.
- [ ] O POST para iniciar competência 1 nessa conta retorna **404**.
- [ ] Volte ao token do usuário principal: suas escolhas e avaliações permanecem.
- [ ] No PUT da segunda conta, envie o corpo abaixo, usando o ID do usuário principal:

```json
{"competencia_ids": [2], "usuario_id": 123}
```

- [ ] Apenas a seleção da conta do token muda. O campo `usuario_id` do corpo
  não é usado; a seleção do usuário principal permanece intacta.

## 8. Erros, autenticação e gravações incompletas

### Cadastro e login públicos

- [ ] Cadastro sem `senha` → **400**.
- [ ] Cadastro com email já usado → **409**.
- [ ] Login com senha errada → **401**.
- [ ] Login sem email → **400**.
- [ ] Acrescente `"papel":"admin"` ao cadastro de uma nova conta QA → **201**,
  mas ela continua `usuario`: após login, criar atividade deve retornar **403**.

### Tokens

- [ ] Remova o token no Authorize: todas as operações protegidas da matriz
  devem retornar **401**. Faça um teste para cada operação, inclusive POST/PUT/PATCH.
- [ ] Autorize com `Bearer invalido`: rotas protegidas retornam **422**.
- [ ] Um token expirado retorna **401**. Esse cenário também está automatizado;
  não há rota de renovação de token implementada. Faça login novamente para obter outro.
- [ ] Cadastro, login, `/dev` e `/apispec_1.json` continuam acessíveis sem token.
- [ ] Não use `OPTIONS` para verificar autenticação: esse método é uma exceção.

### Dados inválidos — usar gestor ou admin para criação

Altere somente o campo indicado no exemplo válido de cada operação:

| Operação | Alteração | Esperado |
|---|---|---|
| POST atividade | Competência 1 e habilidade 7 | 400 |
| POST atividade | `duracao_min: 0` | 400 |
| POST atividade | `questoes: []` | 400 |
| POST atividade | Alternativas da mesma questão com ordem repetida | 400 |
| POST atividade | Uma questão com apenas uma alternativa | 400 |
| POST tarefa | Habilidade inexistente | 400 |
| POST tarefa | `nivel_id: 999999` | 400 |
| POST tarefa | Uma ou seis alternativas | 400 |
| POST tarefa | Ordem de alternativa 0 ou 6 | 400 |
| POST tarefa | Alternativas com ordem repetida | 400 |
| POST atividade ou tarefa | Pontuação negativa, ausente ou com três casas decimais | 400 |
| GET atividades | Filtro `dificuldade=abc` | 400 |
| GET habilidades | Competência inexistente | 404 |
| PUT escolhas | IDs repetidos, inexistentes ou booleanos | 400; seleção anterior preservada |
| POST nivelamento | Competência não escolhida | 404 |
| POST nivelamento | Competência escolhida sem questões | 409; sem avaliação parcial |
| POST nivelamento | Questões com máximo total zero | 409; sem avaliação parcial |

Para testar competência sem questões, confira o cadastro local e selecione uma
que ainda não tenha recebido tarefas. Se todas já tiverem questões, esse caso
pode ser verificado pela suíte automatizada, sem alterar conteúdos locais.

Após uma atividade inválida, confira a listagem para garantir que nenhuma
atividade parcial foi criada. Não há GET editorial de tarefas implementado;
a verificação de ausência de tarefas parciais, de falha real durante o INSERT
e de chamadas concorrentes está na suíte automatizada.

## 9. Testes automatizados

Em outro terminal, na raiz do projeto:

```bash
source venv/bin/activate
python test_models.py
python scripts/testar_banco_local.py
```

A suíte atual tem **38 testes**, incluindo: perfis, autenticação, documentação,
validações, isolamento, rollback após falha real de gravação e duas chamadas
simultâneas para iniciar a mesma avaliação. Ela cria e remove uma base
PostgreSQL descartável, sem usar os dados do banco da aplicação. O usuário do
PostgreSQL precisa ter permissão de criar bases.

Os testes automáticos não dependem das contas QA deste roteiro. Para executar
somente a política de JWT, sem conexão com PostgreSQL:

```bash
python -m unittest discover -s tests -p test_auth_policy.py -v
```

## 10. Limites do fluxo atual e repetição dos testes

- Ainda não existem rotas para enviar respostas, concluir a avaliação,
  calcular o nível, iniciar reavaliação ou executar/concluir atividades.
  O roteiro manual chega até o nivelamento `em_andamento`.
- O status `concluida` e a apresentação de nível são verificados por fixtures
  na suíte automatizada; não são alcançáveis pelo fluxo público atual.
- Não há rotas para editar/excluir atividades e questões, listar usuários,
  desativar contas ou consultar/editar dados pessoais. Essas ações não entram
  na matriz de permissões como funcionalidades disponíveis.
- Repetir POST de criação gera outro conteúdo. Repetir o início da mesma
  avaliação aberta retorna **200** e reutiliza a tentativa.
- O PUT de escolhas substitui a lista inteira. Remover uma competência não
  apaga o histórico nem inicia uma nova tentativa ao reativá-la.
- Para repetir o fluxo desde `pendente`, crie outra conta QA. Não é preciso
  apagar o volume Docker nem o banco. As contas e conteúdos QA permanecem
  disponíveis para os próximos testes locais.
