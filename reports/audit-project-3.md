# Audit Report — Projeto 3: task-manager-api

Saída da skill `/refactor-arch` (Claude Code 2.1.327, modelo Opus) executada em `task-manager-api/`.
A seção Fase 2 é o relatório de auditoria; a Fase 1 aparece antes como contexto.

## Fase 1 — Análise

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.12 (.venv/Scripts/python)
Framework:     Flask 3.0.0
Dependencies:  flask-sqlalchemy 3.1.1 (SQLAlchemy 2.1.9), flask-cors 4.0.0, marshmallow 3.20.1 (unused), requests 2.31.0 (unused), python-dotenv 1.0.0 (unused)
Domain:        Task Manager API (tasks, users, categories, reports)
Architecture:  Partially layered — models/, routes/, services/, utils/ exist, but routes hold validation, business rules and serialization; services/ and most of utils/ are unused; config hardcoded in app.py
Source files:  15 files analyzed (~1158 lines of code)
DB tables:     users, tasks, categories (SQLite via Flask-SQLAlchemy, sqlite:///tasks.db → instance/tasks.db)
Endpoints:     22 routes (GET /, GET /health, GET|POST /tasks, GET|PUT|DELETE /tasks/<id>, GET /tasks/search, GET /tasks/stats, GET|POST /users, GET|PUT|DELETE /users/<id>, GET /users/<id>/tasks, POST /login, GET /reports/summary, GET /reports/user/<id>, GET|POST /categories, PUT|DELETE /categories/<id>)
Entry point:   app.py (python seed.py && python app.py → 0.0.0.0:5000)
================================
```

## Fase 2 — Relatório de auditoria

```text
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   14 analyzed | ~1059 lines of code

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 7 | LOW: 4

## Findings

### [CRITICAL] Credenciais e secrets hardcoded (AP-02)
File: app.py:13, services/notification_service.py:7-10
Description: A chave de sessão do Flask está fixa no código (`app.config['SECRET_KEY'] = 'super-secret-key-123'`). Credenciais SMTP também estão literais no NotificationService (`self.email_user = 'taskmanager@gmail.com'`, `self.email_password = 'senha123'`, host `smtp.gmail.com`). O serviço nunca é usado, mas a credencial fica exposta no repositório do mesmo jeito.
Impact: Qualquer pessoa com acesso ao repositório consegue forjar cookies/sessões assinados com a SECRET_KEY e usar a conta de e-mail. Trocar as credenciais exige editar o código e fazer novo deploy.
Recommendation: Criar config/settings.py que lê SECRET_KEY, DATABASE_URL e SMTP_* de variáveis de ambiente (com fallback de desenvolvimento só para valores não sensíveis) e documentar tudo em .env.example (Playbook P-02).

### [CRITICAL] Armazenamento inseguro de senha / criptografia fraca (AP-04)
File: models/user.py:3, 27-32
Description: `set_password` grava `hashlib.md5(pwd.encode()).hexdigest()`, um hash rápido sem salt e sem iterações. `check_password` compara com `==`, que não é tempo constante.
Impact: Se o banco vazar (ou pela exposição do AP-06), senhas fracas como as do seed ('1234', 'abcd') caem na hora com rainbow tables. A comparação não constante também permite ataques de timing.
Recommendation: Usar `werkzeug.security.generate_password_hash`/`check_password_hash` (já vem com o Flask, nenhuma dependência nova) no model User e manter o seed gerando hashes válidos para as credenciais documentadas (Playbook P-04).

### [CRITICAL] Endpoint perigoso sem autenticação (AP-05)
File: routes/user_routes.py:207-211, 52, 71-72, 78, 119-122, 134-151
Description: `/login` devolve `'token': 'fake-jwt-token-' + str(user.id)` e nenhuma rota valida esse token, então todas as 22 rotas são anônimas. POST /users aceita `role` do cliente (`data.get('role', 'user')`, que aceita 'admin'), e PUT /users/<id> deixa trocar o `role` de qualquer usuário. DELETE /users/<id> apaga o usuário e todas as tasks dele sem nenhuma credencial.
Impact: Qualquer cliente anônimo vira admin com um POST, rebaixa ou desativa outros usuários, ou apaga usuários com todos os dados. O "token" é previsível e não protege nada.
Recommendation: Criar um middleware de autenticação admin (ex.: header com credencial de admin vinda da config) e aplicá-lo nas operações destrutivas e de troca de papel. Anunciar a mudança de contrato no resumo da Fase 3 (Playbook P-05).

### [CRITICAL] Exposição de dados sensíveis (AP-06)
File: models/user.py:21, routes/user_routes.py:33, 85-86, 129, 209
Description: `User.to_dict()` inclui `'password': self.password`, e o resultado é devolvido em GET /users/<id>, POST /users, PUT /users/<id> e POST /login (`'user': user.to_dict()`).
Impact: O hash MD5 de qualquer usuário aparece para qualquer cliente anônimo. Somado ao AP-04, isso entrega as senhas em texto claro. Viola a LGPD.
Recommendation: Tirar `password` da serialização pública de User (to_dict / view de usuário) e anunciar a remoção do campo como mudança de contrato de segurança (Playbook P-06).

### [HIGH] Regra de negócio na rota/controller (Fat Controller) (AP-07)
File: routes/task_routes.py:11-63, 85-154, 156-223, 240-271, 273-299, routes/user_routes.py:42-90, 92-132, 134-151, 153-183, 185-211, routes/report_routes.py:12-101, 103-155, services/notification_service.py:4-48
Description: As rotas validam campos, aplicam regras (overdue, cascade de tasks no delete de usuário, completion_rate), fazem queries, montam dicts manualmente e controlam a transação (`db.session.add/commit/rollback` direto no handler). `summary_report` tem 90 linhas com 4 níveis de aninhamento, e `get_tasks` tem 53. A camada `services/` existe (NotificationService), mas nenhuma rota a usa.
Impact: As regras não podem ser reutilizadas nem testadas sem HTTP. Toda mudança de regra exige mexer em vários handlers grandes, com risco de regressão.
Recommendation: Criar controllers/ (task_controller, user_controller, category_controller, report_controller) com a lógica de negócio e de persistência, deixando as rotas só como mapeamento URL→controller e as regras de domínio (is_overdue, validações) nos models (Playbook P-07).

### [HIGH] Configuração insegura (AP-11)
File: app.py:34, 15, 11
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` liga o debugger do Werkzeug escutando em todas as interfaces. `CORS(app)` libera todas as origens, e a URI do banco (`'sqlite:///tasks.db'`) está fixa no código.
Impact: Execução remota de código pelo console do debugger para qualquer pessoa na rede. Não dá para configurar o comportamento de produção (debug, host, porta, banco, CORS) sem editar o código.
Recommendation: Ler DEBUG (padrão False), HOST, PORT, DATABASE_URL e CORS_ORIGINS da config/ambiente em config/settings.py e montar a app numa factory `create_app()` (Playbook P-02).

### [HIGH] Validação de entrada ausente ou fraca — fluxo de usuários/autenticação (AP-16)
File: routes/user_routes.py:61, 64, 102-103, 106, 115, 124-125
Description: Senha mínima de só 4 caracteres (`len(password) < 4`). A regex de e-mail `^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$` aceita domínios sem TLD. No update, `name` aceita string vazia ou valores que não são texto, e `active` aceita qualquer tipo sem checar se é booleano. Severidade elevada por estar no fluxo de autenticação/dados pessoais.
Impact: Contas com senhas triviais, dados pessoais inválidos persistidos e `active` com valores inesperados que afetam o login (`if not user.active`).
Recommendation: Centralizar a validação de usuário (tipos, e-mail, tamanho mínimo de senha, booleano de active) num validador do domínio usado no create e no update (Playbook P-14).

### [MEDIUM] Estado global mutável (AP-08)
File: services/notification_service.py:6, 31-36
Description: `self.notifications = []` serve de armazenamento em memória das notificações, que `get_notifications` consulta depois. Rebaixado de HIGH para MEDIUM porque o serviço nunca é instanciado (código morto).
Impact: Se for ligado como singleton, as notificações se perdem a cada restart, crescem sem limite e são compartilhadas entre requisições e threads sem sincronização.
Recommendation: Remover o serviço morto ou, se for mantido, persistir as notificações no banco e injetar o serviço nos controllers (Playbook P-08).

### [MEDIUM] Queries N+1 (AP-13)
File: routes/task_routes.py:41-57, 275-281, routes/user_routes.py:22, routes/report_routes.py:15-30, 53-56, 163
Description: `get_tasks` chama `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` para cada task. `get_users` faz `len(u.tasks)`, que dispara um lazy load por usuário. `summary_report` faz `Task.query.filter_by(user_id=u.id).all()` por usuário e mais 12 COUNTs separados (status e prioridade). `get_categories` faz um COUNT por categoria. `task_stats` faz 5 COUNTs mais uma varredura completa.
Impact: O número de queries cresce linearmente com tasks, usuários e categorias, e a latência dos relatórios e listagens cresce junto.
Recommendation: Usar eager loading (`joinedload`/`selectinload`) nas listagens e agregações com `func.count` + `GROUP BY` (status, prioridade, user_id, category_id) nos métodos de consulta do model/controller (Playbook P-09).

### [MEDIUM] Lógica e validação duplicadas (AP-14)
File: routes/task_routes.py:17-39, 71-80, 96-100, 110-114, 167-170, 177, 182, 283-287, 296, routes/user_routes.py:15-23, 61, 71, 106, 120, 162-180, routes/report_routes.py:19-22, 33-37, 67, 132-135, 151, models/task.py:39, 46, 50-60, utils/helpers.py:14-23, 64, 75, 84, 110-111
Description: A regra de atraso (`due_date < datetime.utcnow()` e status diferente de done/cancelled) aparece em 6 lugares, embora já exista `Task.is_overdue()`, que nunca é chamado. A serialização de Task é copiada à mão (task_routes.py:17-28, user_routes.py:162-169) em vez de usar `to_dict()`. A lista de status aparece 5 vezes, a de roles 3 vezes e a regex de e-mail 3 vezes. A validação de título e prioridade é repetida no create e no update, e o cálculo de completion_rate é repetido 3 vezes, apesar de existir `calculate_percentage`.
Impact: As regras divergem com o tempo (ex.: o create aceita priority fora de int, enquanto `process_task_data` converteria), e cada correção precisa ser replicada em vários arquivos.
Recommendation: Concentrar constantes (STATUSES, ROLES, limites) e regras (is_overdue, validação, serialização) no model/validador do domínio, e fazer controllers e views reutilizarem esse código (Playbook P-07, P-14).

### [MEDIUM] Uso de APIs deprecated (AP-15)
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227, routes/user_routes.py:29, 94, 136, 155, routes/report_routes.py:105, 192, 213, models/task.py:15-16, 52, models/category.py:11, models/user.py:14, 29, 32, routes/task_routes.py:31, 72, 215, 285, routes/user_routes.py:172, routes/report_routes.py:35, 42, 45, 71, 133, services/notification_service.py:35, utils/helpers.py:38, seed.py:66-74
Description: `Model.query.get(id)` é API legada desde o SQLAlchemy 2.0 (emite LegacyAPIWarning, e o venv tem SQLAlchemy 2.1.9). `datetime.utcnow()` está deprecated desde o Python 3.12 (o venv usa 3.12.10). MD5 é obsoleto para senha (complemento do AP-04).
Impact: Avisos em runtime e quebra em versões futuras do SQLAlchemy/Python. `utcnow()` devolve datetimes naive, que são ambíguos.
Recommendation: Trocar por `db.session.get(Model, id)`, `datetime.now(timezone.utc)` (gravando naive UTC para manter o formato atual do JSON) e werkzeug.security para senhas (Playbook P-13).

### [MEDIUM] Validação de entrada ausente ou fraca — tasks e categorias (AP-16)
File: routes/task_routes.py:96, 113, 141-144, 167, 182, 210-213, 261, 264, routes/report_routes.py:173-180, 196-202
Description: `len(title)` e `priority < 1` são usados sem checar o tipo (`"priority": "alta"` causa TypeError e responde 500, fora de try). Na busca, `int(priority)` e `int(user_id)` lançam ValueError e respondem 500 para `?priority=abc`. `tags` aceita qualquer tipo. `update_category` faz `'name' in data` sem checar se `request.get_json()` devolveu None (corpo `null` causa TypeError 500), e `color` não é validado, embora `is_valid_color` exista.
Impact: Entradas inválidas viram 500 em vez de 400, e dados inválidos são persistidos (cor arbitrária, tags com tipo inesperado).
Recommendation: Criar validadores por domínio (task/category) que checam tipo e faixa e devolvem 400 com a mesma mensagem de erro, chamados pelos controllers antes de persistir (Playbook P-14).

### [MEDIUM] Tratamento de erro genérico / sem handler central (AP-17)
File: routes/task_routes.py:13, 62-63, 137, 151-154, 204, 221-223, 236, routes/user_routes.py:87-90, 130, 149, routes/report_routes.py:186, 207, 221, services/notification_service.py:23-25, utils/helpers.py:46, 49, 88, app.py:1-34
Description: Há 9 `except:` sem tipo nas rotas, e `get_tasks` envolve o handler inteiro num `try/except:` que devolve `'Erro interno'`. Vários `except Exception as e` só fazem `print`. O padrão try/commit/rollback é repetido em 9 handlers, e não existe `@app.errorhandler`: 404/405/500 do framework voltam como HTML, fora do formato `{'error': ...}` da API.
Impact: Bugs reais ficam invisíveis (sem stack trace em log), as respostas de erro saem em formatos diferentes, e `except:` sem tipo captura até KeyboardInterrupt/SystemExit.
Recommendation: Criar middlewares/error_handler.py com handlers centrais (HTTPException, erros de validação/domínio e Exception, com log), capturar só exceções específicas e deixar o rollback num ponto único (Playbook P-12).

### [MEDIUM] Responsabilidade no módulo errado (AP-18)
File: routes/report_routes.py:157-223, utils/helpers.py:57-116
Description: O CRUD de categorias (GET/POST /categories, PUT/DELETE /categories/<id>) está declarado em `report_routes.py`, no blueprint `reports`. A validação de domínio de task (`process_task_data`) e as constantes de negócio (`VALID_STATUSES`, `VALID_ROLES`, `MIN_PASSWORD_LENGTH`) estão no `utils/helpers.py` genérico.
Impact: Fica difícil achar e manter o código de categorias, e regras de negócio ficam fora do domínio a que pertencem.
Recommendation: Mover as rotas de categoria para routes/category_routes.py com o controller próprio, e as regras/constantes de task e usuário para os models/validadores do domínio (Playbook P-03).

### [LOW] Magic numbers e strings (AP-19)
File: routes/task_routes.py:96, 99, 110, 113, 167, 169, 177, 182, 276-279, routes/user_routes.py:64, 71, 115, 120, routes/report_routes.py:19-28, 45, 129, 180, models/task.py:39, 46, models/category.py:10, app.py:34
Description: Status como strings soltas ('pending', 'done', 'cancelled'), limites 3/200 para título, 1–5 para prioridade, 4 para senha, `t.priority <= 2` como "alta prioridade", janela `timedelta(days=7)`, `'#000000'` e porta 5000 aparecem literais. As constantes em utils/helpers.py:110-116 existem mas não são usadas.
Impact: Mudar uma regra (ex.: prioridade 1–10) exige caçar literais em vários arquivos.
Recommendation: Definir constantes nomeadas no model do domínio (Task.STATUSES, Task.PRIORITY_RANGE etc.) e na config (Playbook P-15).

### [LOW] Nomenclatura ruim (AP-20)
File: routes/task_routes.py:16, 51, routes/user_routes.py:14, routes/report_routes.py:24-28, 55, 158, models/category.py:14, models/task.py:45, models/user.py:27, 29-32
Description: Variáveis de uma letra ou crípticas (`t`, `u`, `c`, `d`, `p`, `cat`, `pwd`) e contadores `p1`…`p5` para prioridades que no JSON se chamam 'critical'…'minimal'. Nomes genéricos (`data`, `result`) em handlers longos.
Impact: Leitura e revisão mais lentas, principalmente nos handlers de relatório.
Recommendation: Renomear variáveis internas (task, user, category, password, priority_counts) mantendo as chaves públicas do JSON (Playbook P-15).

### [LOW] print como logging (AP-21)
File: routes/task_routes.py:149, 153, 219, 234, routes/user_routes.py:83, 89, 147, services/notification_service.py:21, 24, utils/helpers.py:39, 41
Description: Eventos de negócio e erros saem por `print(...)` (ex.: `print(f"Usuário criado: {user.id} - {user.name}")`, `print(f"Erro ao criar task: {str(e)}")`), sem nível nem destino configurável. Alguns incluem dado pessoal (nome do usuário).
Impact: Logs não filtráveis por severidade, perda de stack traces e dados pessoais na saída padrão.
Recommendation: Usar o módulo `logging` (logger por módulo) com níveis info/warning/exception (Playbook P-16).

### [LOW] Código, import ou dependência morta (AP-22)
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, 38-60, models/user.py:34-38, utils/helpers.py:3-7, 9-116, services/notification_service.py:1-48, requirements.txt:4-6
Description: Imports sem uso: `os, sys, json` (app.py), `json, os, sys, time` (task_routes), `hashlib, json` (user_routes), `format_date, calculate_percentage, json` (report_routes), `json` (models/task) e `os, json, sys, math, hashlib` (helpers). `Task.validate_status/validate_priority/is_overdue` e `User.is_admin` nunca são chamados, nenhuma função de utils/helpers.py é chamada, e services/notification_service.py nunca é importado. `marshmallow`, `requests` e `python-dotenv` estão em requirements.txt mas não são importados em lugar nenhum.
Impact: Ruído na leitura, falsa impressão de que existe validação/serviço, e superfície de dependências maior sem necessidade.
Recommendation: Remover imports e funções mortas, reaproveitar o que tiver valor (is_overdue, constantes) nos models, e remover do manifesto as dependências não usadas (Playbook P-16).

## Deprecated APIs
routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227 — `Model.query.get(id)` (legado no SQLAlchemy 2.0) → `db.session.get(Model, id)`
routes/user_routes.py:29, 94, 136, 155 — `Model.query.get(id)` (legado no SQLAlchemy 2.0) → `db.session.get(Model, id)`
routes/report_routes.py:105, 192, 213 — `Model.query.get(id)` (legado no SQLAlchemy 2.0) → `db.session.get(Model, id)`
models/task.py:15, 16, 52; models/category.py:11; models/user.py:14 — `datetime.utcnow` (deprecated no Python 3.12) → `datetime.now(timezone.utc)`
routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133 — `datetime.utcnow()` (deprecated no Python 3.12) → `datetime.now(timezone.utc)`
services/notification_service.py:35; utils/helpers.py:38; seed.py:66, 67, 69, 70, 74 — `datetime.utcnow()` (deprecated no Python 3.12) → `datetime.now(timezone.utc)`
models/user.py:29, 32 — `hashlib.md5` para senha (algoritmo obsoleto para essa finalidade; ver AP-04) → `werkzeug.security.generate_password_hash` / `check_password_hash`

## Endpoint Inventory
GET /health — app.py:22
GET / — app.py:26
GET /tasks — routes/task_routes.py:11
GET /tasks/<int:task_id> — routes/task_routes.py:65
POST /tasks — routes/task_routes.py:85
PUT /tasks/<int:task_id> — routes/task_routes.py:156
DELETE /tasks/<int:task_id> — routes/task_routes.py:225
GET /tasks/search — routes/task_routes.py:240
GET /tasks/stats — routes/task_routes.py:273
GET /users — routes/user_routes.py:10
GET /users/<int:user_id> — routes/user_routes.py:27
POST /users — routes/user_routes.py:42
PUT /users/<int:user_id> — routes/user_routes.py:92
DELETE /users/<int:user_id> — routes/user_routes.py:134
GET /users/<int:user_id>/tasks — routes/user_routes.py:153
POST /login — routes/user_routes.py:185
GET /reports/summary — routes/report_routes.py:12
GET /reports/user/<int:user_id> — routes/report_routes.py:103
GET /categories — routes/report_routes.py:157
POST /categories — routes/report_routes.py:167
PUT /categories/<int:cat_id> — routes/report_routes.py:190
DELETE /categories/<int:cat_id> — routes/report_routes.py:211

================================
Total: 18 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
