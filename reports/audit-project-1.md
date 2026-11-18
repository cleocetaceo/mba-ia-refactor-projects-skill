# Audit Report — Projeto 1: code-smells-project

Saída da skill `/refactor-arch` (Claude Code 2.1.327, modelo Opus) executada em `code-smells-project/`.
A seção Fase 2 é o relatório de auditoria; a Fase 1 aparece antes como contexto.

## Fase 1 — Análise

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.12 (.venv → 3.12.10)
Framework:     Flask 3.1.1
Dependencies:  flask==3.1.1, flask-cors==5.0.1, sqlite3 (stdlib, driver cru com SQL manual), Werkzeug 3.1.9 (transitiva)
Domain:        API de e-commerce (produtos, usuários, pedidos/itens de pedido, relatório de vendas)
Architecture:  Monolítica — 4 arquivos soltos na raiz, sem pastas por camada; models.py (314 linhas) concentra o SQL de 4 domínios; controllers.py atende todos os domínios e também executa SQL; app.py declara rotas admin com SQL inline; database.py mistura conexão global, DDL e seed
Source files:  4 files analyzed (~780 lines of code)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Endpoints:     19 routes (GET /, GET|POST /produtos, GET /produtos/busca, GET|PUT|DELETE /produtos/<id>, GET|POST /usuarios, GET /usuarios/<id>, POST /login, GET|POST /pedidos, GET /pedidos/usuario/<id>, PUT /pedidos/<id>/status, GET /relatorios/vendas, GET /health, POST /admin/reset-db, POST /admin/query)
Entry point:   app.py → `python app.py` (0.0.0.0:5000; loja.db é criado e populado no primeiro boot)
================================
```

## Fase 2 — Relatório de auditoria

```text
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 6 | HIGH: 6 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] SQL Injection (AP-01)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-299
Description: Todas as queries são montadas concatenando strings com valores vindos do request, por exemplo `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` em `login_usuario`, `"INSERT INTO produtos ... VALUES ('" + nome + "', ...` em `criar_produto` e `" AND (nome LIKE '%" + termo + "%' ..."` em `buscar_produtos` (com o termo vindo de `?q=`).
Impact: Permite login sem senha (`' OR '1'='1' --`) e a leitura, alteração ou destruição de qualquer tabela. Também causa erro 500 com qualquer nome que contenha apóstrofo (ex.: "Monitor 27''").
Recommendation: Reescrever todas as queries nos novos models (`models/produto_model.py`, `usuario_model.py`, `pedido_model.py`) usando placeholders `?` e uma tupla de parâmetros. Na busca, montar a cláusula dinamicamente só com placeholders (Playbook P-01).

### [CRITICAL] Credenciais e secrets hardcoded (AP-02)
File: app.py:7, controllers.py:289
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` está fixo no entry point, e o mesmo literal se repete em `health_check` (`"secret_key": "minha-chave-super-secreta-123"`).
Impact: Qualquer pessoa com acesso ao repositório tem a chave usada para assinar sessões e cookies. Trocar a chave exige editar código e fazer deploy.
Recommendation: Criar `config.py` que lê `SECRET_KEY` (e as demais configurações) de variáveis de ambiente, com fallback apenas para desenvolvimento, e documentar em `.env.example` (Playbook P-02).

### [CRITICAL] God Class / God Module (AP-03)
File: models.py:1-314, controllers.py:1-292, database.py:7-86
Description: `models.py` tem 314 linhas e atende 4 domínios (produtos, usuários, pedidos e relatório), misturando SQL e regra de negócio: verificação de estoque e cálculo de total em `criar_pedido` (139-146) e faixas de desconto em `relatorio_vendas` (256-262). `controllers.py` atende os 5 domínios mais o health check com SQL direto. `get_db()` em `database.py` cria a conexão, executa o DDL e insere o seed na mesma função.
Impact: Não dá para testar um domínio isoladamente, e qualquer alteração (ex.: no pedido) arrisca regressão em produtos ou usuários. O arquivo só cresce.
Recommendation: Separar em camadas por domínio: `models/` (acesso a dados por entidade), `services/` (regras de pedido e relatório), `controllers/` (um por domínio), `routes/` (blueprints), `database.py`/`db/` (conexão + schema + seed separados) (Playbook P-03).

### [CRITICAL] Armazenamento inseguro de senha (AP-04)
File: models.py:109-111, 126-129, database.py:75-83
Description: `criar_usuario` grava `senha` em texto puro (`"INSERT INTO usuarios (nome, email, senha, tipo) VALUES ('" + ... + senha + ...`), `login_usuario` compara em SQL com `WHERE ... senha = '" + senha + "'`, e o seed grava `"admin123"`, `"123456"` e `"senha123"` em claro.
Impact: Um vazamento do banco (ou o próprio `/admin/query`) expõe as senhas de todos os usuários, que costumam ser reaproveitadas em outros serviços.
Recommendation: Gerar hash com `werkzeug.security.generate_password_hash` no cadastro e no seed, e verificar com `check_password_hash` no service de autenticação, buscando o usuário só pelo e-mail (Playbook P-04).

### [CRITICAL] Endpoint perigoso sem autenticação (AP-05)
File: app.py:47-57, 59-78, 28
Description: `POST /admin/query` executa SQL arbitrário enviado pelo cliente (`cursor.execute(query)` com `dados.get("sql")`), e `POST /admin/reset-db` apaga as 4 tabelas. Nenhum dos dois verifica credencial. O relatório financeiro `GET /relatorios/vendas` (faturamento, ticket médio) também está aberto a qualquer cliente anônimo.
Impact: Qualquer cliente anônimo tem controle total do banco (ler senhas, apagar dados, escalar o próprio `tipo` para admin) e acesso a dados financeiros.
Recommendation: Mover as rotas admin para um blueprint `admin` protegido por um middleware/decorator que exige token de admin (`ADMIN_TOKEN` via variável de ambiente). O `/admin/query` deve aceitar apenas leitura (`SELECT`). Aplicar a mesma proteção ao relatório financeiro (Playbook P-05).

### [CRITICAL] Exposição de dados sensíveis (AP-06)
File: models.py:83, 99, controllers.py:285-289
Description: `get_todos_usuarios` e `get_usuario_por_id` serializam `"senha": row["senha"]`, então `GET /usuarios` e `GET /usuarios/<id>` devolvem a senha de todos os usuários. O `GET /health` devolve `secret_key`, `db_path`, `debug` e `ambiente`.
Impact: Qualquer cliente obtém as credenciais de todos os usuários (incluindo o admin) e o secret da aplicação. Viola a LGPD.
Recommendation: Criar uma função `to_public_dict` no model de usuário sem o campo `senha`, e reduzir o `/health` a status, conexão com o banco e contagens (Playbook P-06).

### [HIGH] Regra de negócio no controller (AP-07)
File: controllers.py:28-54, 72-90, 208-210, 242-250
Description: Os controllers fazem validação de domínio (lista `categorias_validas`, limites de tamanho de nome, preço e estoque não negativos), disparam efeitos colaterais de domínio (`print("ENVIANDO EMAIL ...")`, `"ENVIANDO SMS"`, `"ENVIANDO PUSH"` em `criar_pedido`) e aplicam regras de transição de status (`if novo_status == "aprovado"` / `"cancelado"`, com a mensagem "Devolver estoque", que nunca é executado).
Impact: As regras não podem ser reutilizadas nem testadas sem HTTP, e a notificação de pedido fica acoplada ao handler.
Recommendation: Mover validações para `services/produto_service.py` e `services/pedido_service.py` (ou validators dedicados), e as notificações para um `services/notification_service.py` chamado pelo service de pedido. O controller fica só com parse do request, chamada ao service e resposta (Playbook P-07).

### [HIGH] Estado global mutável (AP-08)
File: database.py:4-11
Description: A conexão é guardada em `db_connection = None`, reatribuída via `global db_connection` e criada com `sqlite3.connect(db_path, check_same_thread=False)`. Uma única conexão é compartilhada por todas as threads do servidor.
Impact: Há condições de corrida entre requisições concorrentes. Uma transação não finalizada por uma requisição que falhou acaba sendo commitada pela próxima requisição que chamar `commit()`.
Recommendation: Abrir uma conexão por requisição via `flask.g` e fechá-la em `app.teardown_appcontext` (Playbook P-08).

### [HIGH] Acoplamento forte sem injeção de dependência (AP-09)
File: models.py:5, 25, 44, 55, 66, 73, 90, 106, 123, 134, 172, 204, 236, 276, 286, controllers.py:3, 266-274, app.py:4, 49-55, 66-69
Description: Cada função de `models.py` chama o `get_db()` global diretamente. `controllers.py` importa `get_db` e executa `SELECT COUNT(*)` no `health_check`, e `app.py` executa SQL nos handlers admin.
Impact: Não é possível substituir o banco em testes, e a camada HTTP conhece o driver de banco.
Recommendation: Centralizar o acesso à conexão em `database.get_db()` (escopo de requisição) consumido apenas pelos models. Controllers dependem só de services, que dependem só de models (Playbook P-08).

### [HIGH] Escrita multi-etapa sem transação (AP-10)
File: models.py:148-168, 65-70, app.py:51-55
Description: `criar_pedido` faz `INSERT INTO pedidos`, depois `INSERT INTO itens_pedido` e `UPDATE produtos SET estoque = estoque - ...` em loop, sem `try/rollback`. A verificação de estoque (linha 144) e a baixa (163-166) não são atômicas. `deletar_produto` apaga o produto sem tratar os `itens_pedido` que o referenciam. O reset faz 4 `DELETE` sem rollback.
Impact: Uma falha no meio deixa um pedido sem itens ou estoque baixado sem pedido, e na conexão compartilhada essa escrita parcial é commitada por outra requisição. Os itens órfãos aparecem como "Desconhecido".
Recommendation: Executar o pedido inteiro num bloco transacional (`with conn:` / commit e rollback explícitos) dentro do model de pedido, com a verificação de estoque no mesmo bloco (`UPDATE ... WHERE estoque >= ?` checando `rowcount`) (Playbook P-10).

### [HIGH] Configuração insegura (AP-11)
File: app.py:8, 9, 88, controllers.py:286, 288
Description: `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` estão fixos no código, o que expõe o debugger do Werkzeug na rede. `CORS(app)` libera qualquer origem, e o health devolve `"ambiente": "producao"` e `"debug": True` fixos.
Impact: O console do debugger permite execução remota de código por qualquer máquina da rede, e o comportamento de produção não pode ser configurado.
Recommendation: Ler `DEBUG`, `HOST`, `PORT` e `CORS_ORIGINS` de variáveis de ambiente em `config.py`, com debug desligado por padrão (Playbook P-02).

### [HIGH] Validação de entrada ausente no checkout (AP-16)
File: controllers.py:195-201, models.py:139-146
Description: `criar_pedido` não valida `quantidade` (zero ou negativa é aceita: o estoque aumenta e o `total` fica negativo), não verifica se `usuario_id` existe e não agrega itens repetidos. Com `[{produto_id:1, quantidade:10}, {produto_id:1, quantidade:10}]` e estoque 10, os dois itens passam na checagem da linha 144 e o estoque fica -10. Severidade elevada por estar no fluxo de dinheiro.
Impact: É possível criar pedidos com valor negativo, gerar estoque negativo e pedidos de usuários inexistentes, distorcendo o faturamento.
Recommendation: Validar no `pedido_service` que `itens` é uma lista, que `produto_id` e `quantidade` são inteiros com `quantidade > 0` e que o usuário existe, e somar as quantidades por produto antes de checar o estoque (Playbook P-14).

### [MEDIUM] Queries N+1 (AP-13)
File: models.py:187-199, 219-231, 154-156, 239-254
Description: `get_pedidos_usuario` e `get_todos_pedidos` executam `SELECT * FROM itens_pedido` por pedido (`cursor2`) e `SELECT nome FROM produtos` por item (`cursor3`). `criar_pedido` busca o preço de cada produto de novo (linha 155) depois de já tê-lo lido na linha 140. `relatorio_vendas` faz 5 queries separadas (`COUNT`, `SUM` e 3 `COUNT ... WHERE status`).
Impact: A latência cresce linearmente com o número de pedidos e itens.
Recommendation: Buscar itens com `JOIN produtos` filtrando por `pedido_id IN (...)` e agrupar em memória, reaproveitar o preço lido na validação e usar uma única query com `SUM(CASE WHEN status = ? ...)` no relatório (Playbook P-09).

### [MEDIUM] Lógica e validação duplicadas (AP-14)
File: controllers.py:28-46, 72-90, 52, 242, models.py:12-21, 31-40, 304-313, 79-86, 95-102, 171-201, 203-233
Description: O bloco de validação de produto (obrigatórios `nome`/`preco`/`estoque` e não negativos) está copiado entre `criar_produto` e `atualizar_produto`. O mapeamento `row → dict` de produto aparece 3 vezes e o de usuário 2 vezes. `get_pedidos_usuario` e `get_todos_pedidos` são quase idênticas, e as listas de categorias e de status são literais soltos.
Impact: As regras já divergiram (o update não valida categoria nem tamanho do nome), e cada correção precisa ser replicada.
Recommendation: Criar um validador único de produto no service, funções `_row_to_dict` por model, uma função de listagem de pedidos com filtro opcional e constantes `CATEGORIAS_VALIDAS`/`STATUS_VALIDOS` (Playbooks P-07, P-14).

### [MEDIUM] Validação de entrada ausente ou fraca (AP-16)
File: controllers.py:43-50, 87-90, 118-121, 153-158, 169-170, 239-240, 245
Description: `preco`, `estoque` e `nome` não têm o tipo verificado (`"abc" < 0` gera `TypeError` e resposta 500). `atualizar_produto` não aplica as regras de nome e categoria do create. `float(preco_min)` com valor inválido gera 500. `criar_usuario` não valida o formato do e-mail, a força da senha nem e-mail duplicado. `login` e `atualizar_status_pedido` chamam `dados.get(...)` sem checar se `request.get_json()` é `None`, e o update de status devolve 200 para pedido inexistente.
Impact: Erros 500 no lugar de 400, dados inválidos persistidos e contas duplicadas.
Recommendation: Centralizar validadores nos services, levantando erros de validação que um handler central converte em 400 (Playbook P-14).

### [MEDIUM] Tratamento de erro genérico / sem handler central (AP-17)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292, app.py:77-78
Description: Todos os 16 handlers repetem `except Exception as e: return jsonify({"erro": str(e)}), 500`, devolvendo a mensagem interna ao cliente. Não há `@app.errorhandler`, e os formatos de erro variam (`{"erro"}`, `{"erro", "sucesso": False}`, `{"status": "erro", "detalhes"}`).
Impact: Mensagens do SQLite e do Python (estrutura de tabelas, caminhos) vazam para o cliente, e os erros reais não são registrados em log.
Recommendation: Registrar error handlers centrais em `middlewares/error_handler.py` (exceções de domínio → 400/404, inesperadas → 500 genérico + `logger.exception`) e remover os try/except dos controllers (Playbook P-12).

### [MEDIUM] Responsabilidade no módulo errado (AP-18)
File: app.py:32-45, 47-78, database.py:56-84
Description: O entry point `app.py` declara a rota `index` e as rotas administrativas `reset_database` e `executar_query` com SQL inline. Os dados de seed (produtos e usuários) ficam dentro da função de conexão `get_db()`.
Impact: Rotas ficam espalhadas fora da camada de rotas, e o seed roda escondido em qualquer chamada de conexão.
Recommendation: Mover `/` e `/admin/*` para blueprints em `routes/`, com controllers próprios, e o seed para `database/seed.py` chamado na inicialização (Playbook P-03).

### [LOW] Magic numbers e strings (AP-19)
File: models.py:257-262, 150, 247, 250, 253, controllers.py:47-50, 52, 242, 285, app.py:35, 85, 88
Description: As faixas de desconto `10000`/`5000`/`1000` e as taxas `0.1`/`0.05`/`0.02` estão literais no relatório. Os status `'pendente'`, `'aprovado'` e `'cancelado'` aparecem como strings soltas, assim como os limites `2`/`200` do nome, a versão `"1.0.0"` duplicada e a porta `5000` repetida.
Impact: Mudar uma regra comercial exige caçar literais pelo código.
Recommendation: Extrair para constantes nomeadas (`FAIXAS_DESCONTO`, `STATUS_PENDENTE`, `NOME_MIN_LEN`, `API_VERSION`) em módulo de domínio/config (Playbook P-15).

### [LOW] Nomenclatura ruim (AP-20)
File: controllers.py:14, 56, 64, 98, 136, 160, models.py:24, 54, 65, 89, 187, 191, 193, 4, controllers.py:264
Description: Parâmetros e variáveis chamados `id` sobrescrevem o builtin (`id = models.criar_produto(...)`). Há nomes genéricos como `cursor2`, `cursor3` e `prod`, e mistura de idiomas (`get_todos_produtos`, `get_db`, `health_check` ao lado de `listar_produtos`).
Impact: A leitura fica mais difícil e o código fica sujeito a bugs por sombra do builtin.
Recommendation: Renomear apenas as variáveis internas (`produto_id`, `itens_cursor`), padronizar o idioma dos nomes e manter os nomes públicos do contrato (Playbook P-15).

### [LOW] `print` como logging (AP-21)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250, app.py:56, 83-86
Description: Eventos e erros são registrados com `print(...)`, sem níveis de log, incluindo dados pessoais (`print("Login bem-sucedido: " + email)`, `print("Usuário criado: " + email)`).
Impact: Não há níveis nem destino configurável, e e-mails acabam no stdout.
Recommendation: Usar `logging.getLogger(__name__)` com níveis adequados, sem logar PII (Playbook P-16).

### [LOW] Código e imports mortos (AP-22)
File: models.py:2, database.py:2, models.py:122, 63, 70, 283, controllers.py:268
Description: Há imports não usados (`import sqlite3` em `models.py` e `import os` em `database.py`). O parâmetro `tipo` de `criar_usuario` nunca é passado, os `return True` de `atualizar_produto`, `deletar_produto` e `atualizar_status_pedido` nunca são lidos, e `cursor.execute("SELECT 1")` no health tem o resultado descartado.
Impact: É ruído que confunde quem lê e sugere comportamento inexistente.
Recommendation: Remover os imports e retornos não usados na reestruturação (Playbook P-16).

## Deprecated APIs
None detected — verified against catalog AP-15. Não há `datetime.utcnow`/`utcfromtimestamp`, adaptadores datetime do sqlite3 (sem `detect_types`), `before_first_request`, `JSONEncoder`, `safe_str_cmp` nem `pkg_resources`. As APIs de Flask 3.1.1 e flask-cors 5.0.1 usadas são as atuais.

## Endpoint Inventory
GET /produtos — app.py:11 (controllers.py:5)
GET /produtos/busca — app.py:12 (controllers.py:111)
GET /produtos/<int:id> — app.py:13 (controllers.py:14)
POST /produtos — app.py:14 (controllers.py:24)
PUT /produtos/<int:id> — app.py:15 (controllers.py:64)
DELETE /produtos/<int:id> — app.py:16 (controllers.py:98)
GET /usuarios — app.py:18 (controllers.py:128)
GET /usuarios/<int:id> — app.py:19 (controllers.py:136)
POST /usuarios — app.py:20 (controllers.py:146)
POST /login — app.py:21 (controllers.py:167)
POST /pedidos — app.py:23 (controllers.py:188)
GET /pedidos — app.py:24 (controllers.py:229)
GET /pedidos/usuario/<int:usuario_id> — app.py:25 (controllers.py:222)
PUT /pedidos/<int:pedido_id>/status — app.py:26 (controllers.py:237)
GET /relatorios/vendas — app.py:28 (controllers.py:257)
GET /health — app.py:30 (controllers.py:264)
GET / — app.py:32
POST /admin/reset-db — app.py:47
POST /admin/query — app.py:59

================================
Total: 21 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
