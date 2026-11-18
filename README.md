# Skill `refactor-arch` — Refatoração Arquitetural Automatizada

Skill do Claude Code que analisa, audita e refatora projetos backend para o padrão MVC em 3 fases sequenciais (análise, auditoria com pausa para confirmação, refatoração com validação). A mesma skill, sem nenhuma alteração, foi executada nos 3 projetos legados deste repositório:

| Projeto | Stack | Arquitetura original | Findings | Aplicação após Fase 3 |
|---|---|---|---|---|
| `code-smells-project` | Python + Flask | Monolítica | 21 | Sobe e responde 19/19 endpoints |
| `ecommerce-api-legacy` | Node.js + Express | Monolítica (God Class) | 18 | Sobe e responde 3/3 endpoints |
| `task-manager-api` | Python + Flask | Parcialmente em camadas | 18 | Sobe e responde 22/22 endpoints |

- Skill: `<projeto>/.claude/skills/refactor-arch/` (cópia idêntica nos 3 projetos)
- Relatórios da Fase 2: [`reports/audit-project-1.md`](reports/audit-project-1.md), [`reports/audit-project-2.md`](reports/audit-project-2.md), [`reports/audit-project-3.md`](reports/audit-project-3.md)
- Repositório base do desafio: [devfullcycle/mba-ia-refactor-projects-skill](https://github.com/devfullcycle/mba-ia-refactor-projects-skill)

---

## A) Análise Manual

Análise feita lendo o código original (commit `6d1ce62`) antes de escrever a skill. As linhas citadas são do código original. Os problemas estão agrupados por severidade, segundo a escala do desafio.

### Projeto 1 — `code-smells-project` (Python/Flask, API de e-commerce)

4 arquivos na raiz (`app.py`, `controllers.py`, `models.py`, `database.py`), sem nenhuma separação de camadas.

**CRITICAL**

1. **SQL Injection em praticamente todas as queries.** Locais: `models.py:28`, `47-50`, `57-61`, `110`, `127-129`, `140`, `280` e `289-297`. Os valores do usuário são concatenados direto no SQL. No login (`models.py:110`), `' OR '1'='1` autentica sem senha, e a busca (`289-297`) recebe `q` e `categoria` crus da query string.
2. **Secrets hardcoded e expostos pela API.** Locais: `app.py:7` e `controllers.py:285-289`. A `SECRET_KEY` está fixa no código, e o `/health` ainda a devolve junto com `db_path` e `debug` para qualquer cliente.
3. **Endpoints administrativos sem autenticação.** Locais: `app.py:47-57` e `app.py:59-78`. O `POST /admin/reset-db` apaga todas as tabelas, e o `POST /admin/query` executa qualquer SQL enviado no body. Qualquer um na rede pode destruir ou ler o banco inteiro.
4. **Senhas em texto puro, e devolvidas pela API.** Locais: `database.py:75-79`, `models.py:83`, `models.py:99` e `models.py:110`. O seed grava as senhas em claro, o login compara texto puro e `GET /usuarios` lista a senha de todos os usuários.
5. **God Module.** Local: `models.py:1-314`. Um único arquivo concentra o SQL e as regras de 4 domínios (produtos, usuários, pedidos e relatório), e `controllers.py` atende todos eles. Não dá para testar ou alterar um domínio sem mexer nos outros.

**HIGH**

6. **Conexão global compartilhada entre threads.** Local: `database.py:4-11`. Usa `global db_connection` com `check_same_thread=False`, então todas as requisições dividem o mesmo cursor e o mesmo estado de transação.
7. **Pedido sem transação.** Local: `models.py:133-169`. A criação do pedido, dos itens e a baixa de estoque são escritas separadas, sem rollback. Se der erro no meio, as escritas pendentes ficam na conexão global e acabam confirmadas pelo próximo `commit` de outra requisição.
8. **Configuração insegura.** Locais: `app.py:8` e `app.py:88`. `debug=True` com `host="0.0.0.0"` expõe o debugger do Werkzeug, que permite executar código remotamente.

**MEDIUM**

9. **Queries N+1.** Locais: `models.py:187-199` e `models.py:219-231`. Para cada pedido roda 1 query de itens e, para cada item, mais 1 query de produto. A listagem cresce de forma quadrática.
10. **Validação duplicada e incompleta.** Locais: `controllers.py:24-54` e `controllers.py:64-90`. O create e o update repetem o mesmo bloco, mas o update não valida nome nem categoria. Em `controllers.py:188-201`, o pedido não valida `quantidade`.
11. **Tratamento de erro genérico que vaza detalhes internos.** Locais: `controllers.py:10-12` e todos os outros handlers. Cada controller tem `except Exception as e: return {"erro": str(e)}, 500`, que devolve mensagens do SQLite ao cliente e não tem handler central.
12. **Notificações dentro do controller.** Locais: `controllers.py:208-210` e `controllers.py:247-250`. Envio de e-mail, SMS e push (simulados com `print`) misturado ao fluxo HTTP, no módulo errado.

**LOW**

13. **Magic numbers e strings.** Locais: `models.py:256-262`, `controllers.py:52` e `controllers.py:242`. As faixas de desconto (10000/5000/1000 e 10%/5%/2%) e as listas de categorias e de status estão soltas no código.
14. **`print` como logging.** Locais: `controllers.py:8`, `57`, `161`, `179` e `182` e `app.py:56`. Não há níveis de log, e o código registra o e-mail do usuário em texto.
15. **Código morto e nomes ruins.** Locais: `models.py:2` e `database.py:2`. Os imports `sqlite3` e `os` não são usados, há variáveis como `cursor2`, `cursor3` e `prod`, e `id` sobrescreve o builtin (`controllers.py:56`).

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, LMS com checkout)

3 arquivos em `src/`. A classe `AppManager` faz tudo.

**CRITICAL**

1. **Secrets hardcoded.** Local: `src/utils.js:1-7`. Senha do banco de produção (`dbPass`) e chave live do gateway de pagamento (`pk_live_...`) estão versionadas no código.
2. **God Class.** Local: `src/AppManager.js:4-139`. Uma única classe cuida da conexão, do schema, do seed, das 3 rotas, da regra de pagamento e do relatório financeiro.
3. **Criptografia de senha inválida.** Locais: `src/utils.js:17-23` e `src/AppManager.js:68`. `badCrypto` repete os 2 primeiros caracteres do base64 da senha (é reversível e colide com facilidade). Usuários criados sem senha recebem a senha padrão `"123456"`, e o seed grava `'123'` em claro (`AppManager.js:18`).
4. **Número do cartão e chave do gateway no log.** Local: `src/AppManager.js:45`. `console.log` grava o cartão completo e a `paymentGatewayKey` a cada checkout, o que viola o PCI-DSS.
5. **Endpoints administrativos sem autenticação.** Locais: `src/AppManager.js:80` e `src/AppManager.js:131-136`. Qualquer cliente lê o relatório financeiro e apaga usuários.

**HIGH**

6. **Callback hell sem transação.** Local: `src/AppManager.js:37-77`. São 5 níveis de callbacks aninhados. Se o insert do pagamento falhar, a matrícula já foi gravada sem pagamento. O `DELETE` (`131-136`) deixa matrículas e pagamentos órfãos, e a própria resposta admite isso.
7. **Estado global mutável.** Local: `src/utils.js:9-15`. `globalCache` cresce sem limite a cada checkout e nunca é lido.

**MEDIUM**

8. **Queries N+1 no relatório.** Local: `src/AppManager.js:83-127`. Roda 1 query de cursos, mais 1 por curso e mais 2 por matrícula, com contadores manuais (`coursesPending`/`enrPending`) para saber quando responder.
9. **Validação fraca que derruba o processo.** Locais: `src/AppManager.js:35` e `src/AppManager.js:46`. Só verifica se os campos são truthy. Um `card` numérico faz `cc.startsWith` lançar uma exceção dentro do callback e o servidor cai.
10. **Erros mascarados ou ignorados.** Locais: `src/AppManager.js:38` e `src/AppManager.js:133-135`. Um erro de banco vira 404 "Curso não encontrado", e o `DELETE` ignora o `err` e responde sucesso de qualquer jeito.

**LOW**

11. **Nomes ruins.** Locais: `src/AppManager.js:26` e `src/AppManager.js:29-33`. Variáveis como `u`, `e`, `p`, `cid` e `cc`, além de `const self = this`.
12. **Magic strings e regra de pagamento hardcoded.** Local: `src/AppManager.js:46`. `"PAID"`/`"DENIED"` e a regra `startsWith("4")` estão espalhados pelo código.
13. **Código morto e `console.log` como logging.** Locais: `src/utils.js:2`, `5`, `10` e `13`. `dbUser`, `smtpUser` e `totalRevenue` não são usados, e não existe logger com níveis.

### Projeto 3 — `task-manager-api` (Python/Flask, Task Manager)

Já tem `models/`, `routes/`, `services/` e `utils/`, mas as rotas concentram validação, regra de negócio e serialização.

**CRITICAL**

1. **Senha com MD5.** Local: `models/user.py:27-32`. MD5 sem salt é quebrado por rainbow tables em segundos.
2. **Hash da senha exposto pela API.** Local: `models/user.py:21`. O `to_dict()` inclui `password`, que aparece em `GET /users/<id>`, `POST /users` e `POST /login` (`routes/user_routes.py:33`, `85` e `209`).
3. **Escalada de privilégio e autenticação falsa.** Locais: `routes/user_routes.py:52`, `71-78`, `119-122`, `134-151` e `210`. Qualquer cliente cria ou promove um usuário para `admin` só enviando `role`, apaga usuários sem autenticação, e o "token" do login é `fake-jwt-token-<id>`.
4. **Secrets hardcoded.** Locais: `app.py:13` e `services/notification_service.py:7-10`. `SECRET_KEY` e a senha SMTP estão fixas no código.

**HIGH**

5. **Fat routes.** Locais: `routes/task_routes.py:85-154` e `156-223`. Validação, regras e persistência ficam dentro dos handlers. Existe um `process_task_data` em `utils/helpers.py:57-108` que nunca é usado.
6. **Configuração insegura.** Local: `app.py:34`. `debug=True` com `host='0.0.0.0'`.

**MEDIUM**

7. **Queries N+1.** Locais: `routes/task_routes.py:41-57`, `routes/report_routes.py:55-61` e `159-164`, e `routes/user_routes.py:22`. `GET /tasks` faz 2 queries extras por task, e o relatório faz 1 query por usuário mais 12 COUNTs separados.
8. **APIs deprecated.** Locais: `Model.query.get()` em `routes/task_routes.py:42`, `67`, `117` e outros (legado no SQLAlchemy 2.0, substituído por `db.session.get`). `datetime.utcnow()` em `models/task.py:15-16` e outros (deprecated no Python 3.12, substituído por `datetime.now(timezone.utc)`).
9. **Regra de atraso duplicada em 6 lugares.** Locais: `routes/task_routes.py:30-39`, `71-80` e `283-287`, `routes/report_routes.py:33-43` e `132-135`, e `routes/user_routes.py:171-180`. Isso apesar de existir `Task.is_overdue()` em `models/task.py:50-60`, que ninguém chama.
10. **`except:` sem tipo.** Locais: `routes/task_routes.py:62`, `137` e `236` e `routes/report_routes.py:186`, `207` e `221`. Engole qualquer erro, inclusive bugs, e não existe handler central.
11. **CRUD de categorias no módulo errado.** Local: `routes/report_routes.py:157-223`. As rotas de categorias estão no blueprint de relatórios.

**LOW**

12. **Imports mortos.** Locais: `app.py:7`, `routes/task_routes.py:7` e `utils/helpers.py:2-7`. `os`, `sys`, `json`, `time`, `math` e `hashlib` são importados e não usados.
13. **Magic numbers.** Locais: `routes/report_routes.py:24-28`, `45` e `129`. Prioridades 1 a 5, `<= 2` como "alta prioridade" e `timedelta(days=7)`. As constantes de `utils/helpers.py:110-116` existem, mas não são usadas.
14. **`print` como logging.** Locais: `routes/user_routes.py:83` e `routes/task_routes.py:149`. Sem níveis, e o nome do usuário vai para o log.

---

## B) Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                                  # o "prompt": fases, regras e formatos de saída (138 linhas)
└── references/
    ├── 01-project-analysis.md                # Fase 1: heurísticas de stack, banco, entry point e arquitetura
    ├── 02-anti-patterns-catalog.md           # Fase 2: 22 anti-patterns com sinais de detecção e severidade
    ├── 03-audit-report-template.md           # Fase 2: template fixo do relatório e exemplos de finding bom e ruim
    ├── 04-mvc-architecture-guidelines.md     # Fase 3: camadas, layouts alvo por stack, regras transversais
    └── 05-refactoring-playbook.md            # Fase 3: 16 transformações com código antes/depois (Python e JS)
```

### Decisões de design

- **O SKILL.md orquestra e as referências guardam o conhecimento.** O SKILL.md tem só o fluxo (o que fazer, em que ordem, que formato imprimir) e uma tabela dizendo qual referência ler em cada fase. Assim o contexto fica enxuto: a Fase 1 não carrega o playbook de 644 linhas.
- **`disable-model-invocation: true`.** A skill altera muitos arquivos, então só roda quando invocada explicitamente com `/refactor-arch`, nunca por iniciativa do modelo.
- **Regras invioláveis no topo do SKILL.md.** Fases estritamente sequenciais. Nenhuma escrita em disco nas Fases 1 e 2. A Fase 2 termina com `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e para. Todo finding precisa de evidência real (arquivo e linha). O contrato HTTP é preservado e o comando de boot original é mantido. Não pode tocar em `.claude/`, `.git/`, venvs, `node_modules` e lockfiles, nem adicionar dependências.
- **Contrato HTTP como restrição explícita.** As guidelines listam as únicas mudanças de contrato permitidas, todas de segurança: remover campos sensíveis das respostas, exigir `X-Admin-Token` em endpoints destrutivos, ignorar `role`/`tipo` vindo do cliente e trocar o hash de senha mantendo o login do seed funcionando. Qualquer outra mudança tem que ser listada em "Contract Changes".
- **Validação com linha de base.** Antes de alterar qualquer coisa, a Fase 3 sobe a aplicação original e grava status e chaves JSON de cada endpoint. Depois da refatoração, compara com essa gravação. "Funciona" passa a ser um critério objetivo.
- **Template de relatório rígido.** Mesmos rótulos (`File`, `Description`, `Impact`, `Recommendation (Playbook P-XX)`), ordenação CRITICAL → LOW, seções de APIs deprecated e de inventário de endpoints. Cada finding aponta para o padrão do playbook que o corrige, o que liga a Fase 2 à Fase 3.

### Catálogo de anti-patterns (22)

| Severidade | Anti-patterns |
|---|---|
| CRITICAL | AP-01 SQL Injection · AP-02 Secrets hardcoded · AP-03 God Class/Module · AP-04 Senha/cripto fraca · AP-05 Endpoint perigoso sem auth · AP-06 Exposição de dados sensíveis |
| HIGH | AP-07 Fat Controller · AP-08 Estado global mutável · AP-09 Acoplamento sem DI · AP-10 Escrita sem transação · AP-11 Configuração insegura · AP-12 Callback hell |
| MEDIUM | AP-13 N+1 · AP-14 Duplicação · AP-15 APIs deprecated · AP-16 Validação ausente · AP-17 Erro genérico · AP-18 Responsabilidade no módulo errado |
| LOW | AP-19 Magic numbers · AP-20 Nomenclatura · AP-21 print/console.log · AP-22 Código morto |

Os anti-patterns saíram da análise manual: cada problema da seção A virou uma entrada com sinais de detecção concretos (por exemplo, "query SQL montada com `+`/f-string/template string a partir de input", e não "código inseguro"). O AP-15 tem uma tabela de APIs obsoletas e seus equivalentes modernos para Python, SQLAlchemy, Flask, Node e Express. O catálogo também traz regras de ajuste de severidade: sobe um nível em fluxos de dinheiro ou autenticação e desce em código morto. Fechei em 6/6/6/4 para cobrir com folga o mínimo de 8 anti-patterns com severidade distribuída.

### Como garanti que a skill é agnóstica de tecnologia

- **Detecção por evidência, não por suposição.** A Fase 1 identifica linguagem, framework e banco pelos manifestos (`requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`, etc.) e pelos imports, usando tabelas de heurísticas. Também detecta venv local e o comando de boot real.
- **Sinais de detecção descritos pelo conceito.** Cada anti-pattern é descrito de forma independente de linguagem, com exemplos em Python e em JavaScript. O playbook traz o antes/depois nas duas linguagens.
- **Layout MVC por stack.** As guidelines definem um layout alvo para Flask (`src/{config,database,models,controllers,views,services,middlewares}`) e outro para Express (`src/{config,database,models,controllers,routes,services,middlewares}`), além de um mapeamento genérico de camadas para outras stacks.
- **Estratégia adaptada ao nível de organização.** No passo 3.1, a skill classifica o projeto. Um monolito é reestruturado em `src/`. Um projeto parcialmente em camadas evolui no lugar: as pastas existentes são mantidas e as camadas que faltam são criadas. Foi o que aconteceu no `task-manager-api`, que ganhou `controllers/`, `middlewares/` e `config/` sem perder `models/` e `routes/`.
- **Prova prática.** A mesma pasta (hash idêntico nos 3 projetos) rodou em Flask monolítico, em Express com God Class e em Flask parcialmente organizado, sem nenhum ajuste por projeto.

### Desafios e soluções

- **Versão do Claude Code.** A 2.1.157 recusava o modelo ("does not support this model"). Resolvido com `claude update` (para a 2.1.327). O modelo padrão exigia créditos extras, então as execuções usaram `--model opus`.
- **Pausa da Fase 2 em modo headless.** Com `claude -p`, cada chamada é um turno. A Fase 2 termina e o processo sai, aguardando a confirmação. A Fase 3 é disparada com `claude -p "y" --continue`, que retoma a mesma sessão. A pausa funcionou nos 3 projetos: `git status` não mostrou nenhuma alteração nos fontes entre as duas chamadas.
- **Saída incompleta no modo `-p`.** O `-p` imprime só a última mensagem, então o bloco da Fase 1 não aparecia no log. Os relatórios foram extraídos do transcript da sessão (`~/.claude/projects/.../*.jsonl`), onde estão as mensagens completas das Fases 1 e 2.
- **Encoding no Windows.** O `Tee-Object` do PowerShell grava UTF-16, o que quebrava a leitura dos logs em Python. Resolvido detectando o BOM, e depois lendo direto do transcript JSONL.
- **Mudanças de segurança × contrato.** Proteger `/admin/*` e apagar `senha` das respostas altera o contrato. A solução foi listar essas mudanças na skill como as únicas permitidas e exigir que o resumo final as declare em "Contract Changes". Os endpoints protegidos respondem 401 sem token, 403 se `ADMIN_TOKEN` não estiver configurado e exatamente a resposta original com o token.
- **Bancos de dados da linha de base.** Capturar a linha de base cria `loja.db` e `instance/tasks.db`. Eles são apagados antes de cada execução, para a skill partir do estado original.

---

## C) Resultados

### Resumo das auditorias

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | APIs deprecated |
|---|---|---|---|---|---|---|
| 1 — code-smells-project | 6 | 6 | 5 | 4 | 21 | Nenhuma encontrada |
| 2 — ecommerce-api-legacy | 5 | 6 | 3 | 4 | 18 | Nenhuma encontrada |
| 3 — task-manager-api | 4 | 3 | 7 | 4 | 18 | `Model.query.get`, `datetime.utcnow`, MD5 |

Todos os problemas da análise manual foram encontrados pela skill nos 3 projetos, com arquivo e linhas. A skill também achou problemas que eu não tinha listado. Um exemplo é o checkout do projeto 1: itens repetidos no mesmo pedido passam separadamente pela checagem de estoque e deixam o estoque negativo.

### Antes e depois

**Projeto 1 — code-smells-project** (monolito → `src/` em camadas)

```
ANTES                         DEPOIS
app.py                        app.py                      # entry point fino: create_app() + run
controllers.py                .env.example
models.py                     src/
database.py                   ├── app.py                  # composition root
requirements.txt              ├── config/settings.py
                              ├── database/{connection,schema,seed}.py
                              ├── models/{produto,usuario,pedido,admin}_model.py
                              ├── controllers/{produto,usuario,pedido,relatorio,sistema,admin}_controller.py, validators.py
                              ├── views/{produto,usuario,pedido,relatorio,sistema,admin}_routes.py
                              ├── services/{password,notification}_service.py
                              └── middlewares/{error_handler,auth}.py
```

**Projeto 2 — ecommerce-api-legacy** (God Class → camadas com injeção de dependência)

```
ANTES                         DEPOIS
src/app.js                    src/app.js                  # composition root: config, banco, DI, rotas
src/AppManager.js             src/config/index.js
src/utils.js                  src/database/{connection,schema}.js     # Promises + transaction()
api.http                      src/models/{user,course,enrollment,payment,auditLog}.model.js
package.json                  src/controllers/{checkout,report,user}.controller.js, validators.js
                              src/routes/{index,checkout,report,user}.routes.js
                              src/services/{password,payment}.service.js
                              src/middlewares/{adminAuth,errorHandler}.js
                              src/utils/{logger,errors,asyncHandler}.js
                              .env.example · api.http (com X-Admin-Token) · package.json (inalterado)
```

**Projeto 3 — task-manager-api** (parcialmente em camadas → MVC completo, evoluindo no lugar)

```
ANTES                         DEPOIS
app.py                        app.py                      # create_app(), exporta app/db (seed.py continua funcionando)
database.py                   database.py · seed.py · .env.example
seed.py                       config/settings.py          # NOVO
models/{user,task,category}   models/{user,task,category} # serialização com allowlist, is_overdue() único
routes/{task,user,report}     routes/{task,user,report,category,health}_routes.py   # handlers de 1–3 linhas
services/notification_service controllers/{task,user,category,report}_controller.py, base.py, validators.py  # NOVO
utils/helpers.py              middlewares/{error_handler,auth}.py                   # NOVO
                              services/token_service.py · utils/helpers.py
```

### Checklist de validação

Os 3 projetos passaram em todos os itens:

| Item | P1 | P2 | P3 |
|---|---|---|---|
| **Fase 1** Linguagem detectada corretamente | ✅ Python 3.12 | ✅ JavaScript (Node) | ✅ Python 3.12 |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express 4.x | ✅ Flask 3.0.0 |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS com checkout | ✅ Task Manager |
| Nº de arquivos condiz com a realidade | ✅ 4 | ✅ 3 | ✅ 15 (14 no relatório)¹ |
| **Fase 2** Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Findings ordenados CRITICAL → LOW | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 21 | ✅ 18 | ✅ 18 |
| Detecção de APIs deprecated (se aplicável) | ✅ nenhuma | ✅ nenhuma | ✅ 3 tipos |
| Pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3** Estrutura de diretórios MVC | ✅ | ✅ | ✅ |
| Configuração extraída (sem hardcoded) | ✅ | ✅ | ✅ |
| Models abstraem os dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ `views/` | ✅ `routes/` | ✅ `routes/` |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ | ✅ | ✅ |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem corretamente | ✅ 19/19 | ✅ 3/3 | ✅ 22/22 |

¹ O projeto 3 tem 15 arquivos `.py`, três deles `__init__.py` vazios. A Fase 1 contou os 15, e o cabeçalho do relatório contou 14.

### Logs das aplicações rodando após a refatoração

Além da validação feita pela própria skill, rodei um smoke test independente em cada projeto, com `ADMIN_TOKEN=dev-token`. A coluna da direita mostra o status HTTP. Os mesmos casos foram executados na versão original antes da refatoração e retornaram os mesmos status. A única diferença são os endpoints que passaram a exigir token, que respondem 401 sem o header e o status original com ele (`[admin]`).

**Projeto 1** — `python app.py` → `Running on http://127.0.0.1:5000`, `Debug mode: off`

```
GET    /                          -> 200    POST   /login (válido)            -> 200
GET    /health                    -> 200    POST   /login (senha errada)      -> 401
GET    /produtos                  -> 200    POST   /pedidos                   -> 201
GET    /produtos/busca?q=Mouse    -> 200    GET    /pedidos                   -> 200
GET    /produtos/1                -> 200    GET    /pedidos/usuario/2         -> 200
GET    /produtos/9999             -> 404    PUT    /pedidos/1/status          -> 200
POST   /produtos                  -> 201    GET    /relatorios/vendas         -> 401
POST   /produtos (inválido)       -> 400    GET    /relatorios/vendas [admin] -> 200
PUT    /produtos/1                -> 200    POST   /admin/query               -> 401
GET    /usuarios                  -> 200    POST   /admin/query [admin]       -> 200
GET    /usuarios/1                -> 200    DELETE /produtos/11               -> 200
POST   /usuarios                  -> 201    POST   /admin/reset-db [admin]    -> 200
```

`GET /usuarios` agora devolve `{"email","id","nome","tipo","criado_em"}`, sem `senha`. O `/health` devolve `"debug": false` e não tem mais `secret_key`.

**Projeto 2** — `npm start` → `[INFO] LMS API rodando na porta 3000...`

```
POST   /api/checkout (cartão 4…)        -> 200  {"msg":"Sucesso","enrollment_id":2}
POST   /api/checkout (cartão recusado)  -> 400
POST   /api/checkout (campos faltando)  -> 400
POST   /api/checkout (curso inexistente)-> 404
GET    /api/admin/financial-report      -> 401
GET    /api/admin/financial-report [admin] -> 200  [{"course":"Clean Architecture","revenue":997,...}]
DELETE /api/users/1                     -> 401
DELETE /api/users/1 [admin]             -> 200
```

O log de pagamento agora sai como `Pagamento de 497 no cartão **** 4444: PAID`, sem o número completo e sem a chave do gateway.

**Projeto 3** — `python seed.py && python app.py` → `Running on http://127.0.0.1:5000`, `Debug mode: off`

```
GET  /                  -> 200    GET  /tasks/9999          -> 404
GET  /health            -> 200    POST /tasks               -> 201
GET  /users             -> 200    PUT  /tasks/1             -> 200
GET  /users/1           -> 200    GET  /tasks/search?q=API  -> 200
GET  /users/1/tasks     -> 200    GET  /tasks/stats         -> 200
POST /users             -> 201    GET  /reports/summary     -> 200
PUT  /users/2           -> 200    GET  /reports/user/1      -> 200
POST /login             -> 200    GET  /categories          -> 200
POST /login (errada)    -> 401    POST /categories          -> 201
GET  /tasks             -> 200    PUT  /categories/1        -> 200
GET  /tasks/1           -> 200    DELETE /users/3           -> 401
                                  DELETE /users/3 [admin]   -> 200
```

O login com a credencial do seed (`joao@email.com` / `1234`) continua funcionando, agora com hash scrypt. A resposta não traz mais `password`, e o token passou a ser assinado (itsdangerous) em vez de `fake-jwt-token-<id>`.

### Mudanças de contrato (todas por segurança)

- **P1:** `senha` foi removida de `/usuarios`, e `secret_key` e `db_path` foram removidos de `/health`. `/admin/reset-db`, `/admin/query` e `/relatorios/vendas` exigem `X-Admin-Token`. O campo `tipo` enviado no cadastro é ignorado. O DELETE de produto virou exclusão lógica.
- **P2:** `/api/admin/financial-report` e `DELETE /api/users/:id` exigem `X-Admin-Token`. Um usuário novo precisa enviar `pwd` (a senha padrão `123456` deixou de existir). O DELETE agora remove também as matrículas e pagamentos do usuário, em transação.
- **P3:** `password` foi removido das respostas. `DELETE /users/<id>` exige `X-Admin-Token`. `role` só é aplicado quando a requisição traz um token de admin válido. O `token` do login passou a ser assinado.

### Comportamento em stacks diferentes

- **Flask monolítico (P1):** reestruturação completa em `src/`, com `views/` como camada de rotas. Foi o caso com mais findings CRITICAL, por causa do SQL injection em praticamente todas as queries. As queries foram parametrizadas e o N+1 foi resolvido com `LEFT JOIN`. A conexão global virou conexão por requisição em `flask.g`.
- **Express (P2):** a skill identificou o AP-12 (callback hell), que é específico de JS. Converteu o `sqlite3` para Promises/`async-await` sem adicionar dependências, colocou o checkout numa transação e passou a autorizar o pagamento antes de qualquer escrita. Usou `routes/` como camada View, que é a convenção do Express. Já na Fase 2, a skill rodou o app para confirmar dois achados: o vazamento do cartão no log e a queda do servidor com um `card` numérico.
- **Flask parcialmente organizado (P3):** a skill não descartou a estrutura existente. Manteve `models/` e `routes/`, criou só as camadas que faltavam (`controllers/`, `middlewares/`, `config/`) e removeu o serviço morto. Foi o único projeto com APIs deprecated, todas substituídas, e o boot e o seed passaram a rodar sem nenhum `DeprecationWarning`. As dependências não usadas (`marshmallow`, `requests`) saíram do `requirements.txt`.
- **Em todos:** nenhuma dependência nova foi adicionada, o comando de boot original continua funcionando e o DEBUG passou a ser desligado por padrão.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (testado na versão 2.1.327; rode `claude update` se o modelo for recusado)
- Python 3.12+ (projetos 1 e 3) e Node.js 20.12+ (projeto 2)
- Dependências de cada projeto:

```bash
cd code-smells-project && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Linux/macOS: .venv/bin/pip
cd ../ecommerce-api-legacy && npm install
cd ../task-manager-api && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
```

### Executar a skill

**Modo interativo (recomendado):** a skill para no fim da Fase 2 e espera você responder `y`.

```bash
cd code-smells-project   # ou ecommerce-api-legacy / task-manager-api
claude "/refactor-arch"
```

**Modo headless:** foi o modo usado para gerar os resultados deste repositório. A primeira chamada executa as Fases 1 e 2 e para; a segunda confirma e executa a Fase 3 na mesma sessão.

```bash
claude -p "/refactor-arch" --model opus --permission-mode acceptEdits \
  --allowedTools "Bash,Read,Glob,Grep,Edit,Write" --output-format text

claude -p "y" --continue --model opus --permission-mode acceptEdits \
  --allowedTools "Bash,Read,Glob,Grep,Edit,Write" --output-format text
```

Para executar em outro projeto, copie a pasta `.claude/skills/refactor-arch/` para a raiz dele e rode o mesmo comando.

### Validar a refatoração

Depois de refatorados, os endpoints administrativos exigem o header `X-Admin-Token` com o valor de `ADMIN_TOKEN`. Sem a variável configurada, eles respondem 403. Cada projeto tem um `.env.example` com todas as variáveis.

```powershell
# Projeto 1 — http://127.0.0.1:5000
cd code-smells-project
$env:ADMIN_TOKEN = "dev-token"; .venv\Scripts\python app.py
curl http://127.0.0.1:5000/produtos
curl -H "X-Admin-Token: dev-token" http://127.0.0.1:5000/relatorios/vendas

# Projeto 2 — http://localhost:3000
cd ecommerce-api-legacy
$env:ADMIN_TOKEN = "dev-token"; npm start
# use as requisições de api.http (já incluem o X-Admin-Token)

# Projeto 3 — http://127.0.0.1:5000
cd task-manager-api
.venv\Scripts\python seed.py
$env:ADMIN_TOKEN = "dev-token"; .venv\Scripts\python app.py
curl http://127.0.0.1:5000/tasks
```

No bash, use `ADMIN_TOKEN=dev-token python app.py` (ou `npm start`). Confira que a aplicação sobe sem traceback, que os endpoints originais respondem com os mesmos status de antes e que os endpoints protegidos respondem 401 sem o header e 200 com ele.
