# Audit Report — Projeto 1: code-smells-project

Saída da skill `/refactor-arch` (Claude Code 2.1.327, modelo Opus) executada em `code-smells-project/`.
A seção Fase 2 é o relatório de auditoria; a Fase 1 aparece antes como contexto.

## Fase 1 — Análise

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.12 (.venv)
Framework:     Flask 3.1.1
Dependencies:  flask==3.1.1, flask-cors==5.0.1, sqlite3 (stdlib, raw driver)
Domain:        E-commerce API (produtos, usuários, pedidos/itens, relatório de vendas)
Architecture:  Monolítica — 4 arquivos na raiz, sem pastas por camada; models.py (314 linhas) concentra o SQL de 4 domínios, app.py mistura config, rotas e SQL administrativo
Source files:  4 files analyzed (~780 lines of code)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Endpoints:     19 routes (GET /, GET|POST /produtos, GET /produtos/busca, GET|PUT|DELETE /produtos/<id>, GET|POST /usuarios, GET /usuarios/<id>, POST /login, GET|POST /pedidos, GET /pedidos/usuario/<id>, PUT /pedidos/<id>/status, GET /relatorios/vendas, GET /health, POST /admin/reset-db, POST /admin/query)
Entry point:   app.py → `python app.py` (0.0.0.0:5000; loja.db criado e populado no boot)
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
CRITICAL: 7 | HIGH: 5 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] SQL Injection (AP-01)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-297
Description: Todas as queries são montadas por concatenação, ex.: "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'" em login_usuario, "nome LIKE '%" + termo + "%'" em buscar_produtos (vem de ?q=) e "SELECT * FROM produtos WHERE id = " + str(item["produto_id"]) com produto_id lido do corpo de POST /pedidos.
Impact: Permite burlar o login (' OR '1'='1 no email), ler/alterar/apagar qualquer tabela pela busca de produtos ou pelo checkout.
Recommendation: Reescrever todas as queries nos novos models por domínio usando placeholders "?" com tupla de parâmetros, inclusive a busca dinâmica (lista de condições + lista de params) (Playbook P-01).

### [CRITICAL] Credenciais e secrets hardcoded (AP-02)
File: app.py:7, controllers.py:289
Description: app.config["SECRET_KEY"] = "minha-chave-super-secreta-123" está fixo no código, e o mesmo literal foi copiado em health_check.
Impact: Quem tem acesso ao repositório tem a chave de assinatura; trocar a chave exige editar o código e fazer deploy.
Recommendation: Criar config/settings.py que lê SECRET_KEY de variável de ambiente (com fallback aleatório em dev) e documentar em .env.example (Playbook P-02).

### [CRITICAL] God Class / God Module (AP-03)
File: models.py:1-314, controllers.py:1-292, database.py:7-86
Description: models.py tem 314 linhas e atende 4 domínios (produtos, usuários, pedidos, relatório); controllers.py junta handlers de 5 domínios + health; get_db() em database.py cuida ao mesmo tempo de conexão, criação de schema (14-54) e seed (56-84).
Impact: Não dá para testar um domínio isolado; qualquer mudança arrisca regressão nos outros; o arquivo cresce sem limite.
Recommendation: Separar por camada e domínio: src/models/{produto,usuario,pedido,relatorio}_model.py, src/controllers/*_controller.py, src/views/*_routes.py (Blueprints), src/database/{connection,schema,seed}.py (Playbook P-03).

### [CRITICAL] Armazenamento inseguro de senha (AP-04)
File: database.py:76-78, models.py:109-111, 126-129
Description: As senhas são gravadas em texto puro (seed "admin123", "123456", "senha123"; INSERT de senha em criar_usuario) e comparadas direto no SQL (WHERE ... senha = '" + senha + "').
Impact: Um vazamento do banco expõe a senha de todo mundo (e o reuso dela em outros serviços); junto com AP-06, as senhas já saem pela API.
Recommendation: Usar werkzeug.security.generate_password_hash/check_password_hash num password_service; buscar o usuário pelo email e verificar o hash na aplicação; o seed grava hashes mantendo as credenciais documentadas (Playbook P-04).

### [CRITICAL] Endpoint perigoso sem autenticação (AP-05)
File: app.py:47-57, 59-78, 28
Description: POST /admin/reset-db apaga as 4 tabelas, e POST /admin/query executa cursor.execute(dados["sql"]) com qualquer SQL vindo do cliente (inclusive DROP/DELETE, com commit), os dois sem nenhuma credencial. GET /relatorios/vendas mostra faturamento e ticket médio para qualquer cliente anônimo.
Impact: Qualquer cliente anônimo apaga ou altera o banco inteiro, lê a tabela de usuários (com senhas) e vê dados financeiros.
Recommendation: Criar o middleware require_admin (token via ADMIN_TOKEN no header) e aplicá-lo às rotas /admin/* e ao relatório financeiro; restringir /admin/query a uma única sentença SELECT (400 para o resto) (Playbook P-05).

### [CRITICAL] Exposição de dados sensíveis (AP-06)
File: models.py:83, 99, controllers.py:285-289
Description: get_todos_usuarios e get_usuario_por_id serializam "senha": row["senha"], então GET /usuarios e GET /usuarios/<id> devolvem as senhas. GET /health devolve "secret_key", "db_path", "debug" e "ambiente".
Impact: Qualquer cliente obtém as senhas de todos os usuários (incluindo o admin) e a SECRET_KEY da aplicação; isso viola a LGPD.
Recommendation: Remover "senha" da serialização de usuário e tirar secret_key/db_path/debug da resposta do health (Playbook P-06).

### [CRITICAL] Escrita multi-etapa sem transação (AP-10)
File: models.py:133-169
Description: criar_pedido faz INSERT em pedidos, depois um loop de INSERT em itens_pedido + UPDATE de estoque, sem BEGIN/ROLLBACK. Usa a conexão global compartilhada, e a checagem de estoque (144) é separada da baixa (163-166). Severidade elevada de HIGH: é um fluxo de dinheiro (total do pedido e estoque).
Impact: Uma falha no meio do loop deixa pedido sem itens ou estoque baixado pela metade, e o próximo commit de qualquer outra requisição na mesma conexão grava esse lixo; pedidos concorrentes podem vender acima do estoque.
Recommendation: Rodar o pedido inteiro num bloco transacional (with conn: / rollback em exceção) dentro de um pedido_service, com baixa condicional "UPDATE ... SET estoque = estoque - ? WHERE id = ? AND estoque >= ?" (Playbook P-10).

### [HIGH] Regra de negócio na rota/controller (AP-07)
File: controllers.py:43-54, 208-210, 242-250
Description: Os controllers aplicam regra de domínio: faixa de preço/estoque, tamanho do nome e categorias válidas em criar_produto; "ENVIANDO EMAIL/SMS/PUSH" em criar_pedido; lista de status válidos e notificações de aprovação/cancelamento em atualizar_status_pedido.
Impact: As regras não podem ser reutilizadas nem testadas sem HTTP; a notificação fica presa ao handler.
Recommendation: Controllers só leem o request e montam a resposta; regras vão para validators/services (produto_service, pedido_service) e as notificações para notification_service (Playbook P-07).

### [HIGH] Estado global mutável (AP-08)
File: database.py:4, 8-11
Description: db_connection é um singleton de módulo reatribuído com "global db_connection" e aberto com sqlite3.connect(db_path, check_same_thread=False), compartilhado entre todas as threads do servidor.
Impact: Condições de corrida e transações misturadas entre requisições (um commit de uma requisição grava escritas pendentes de outra).
Recommendation: Uma conexão por requisição guardada em flask.g, fechada no teardown_appcontext, com o caminho do banco vindo da config (Playbook P-08).

### [HIGH] Acoplamento forte sem injeção de dependência (AP-09)
File: models.py:5, 25, 44, 55, 66, 73, 90, 106, 123, 134, 172, 204, 236, 276, 286, controllers.py:3, 266-274, app.py:4, 49-55, 66-69
Description: Todas as 15 funções de models.py chamam o get_db() global. health_check (controllers.py) e as rotas admin (app.py) importam get_db e executam SQL direto, sem passar por model.
Impact: Não dá para trocar o banco nem injetar um fake em teste; mudar a infraestrutura exige editar controllers e o entry point.
Recommendation: Models recebem a conexão pelo provider da camada database (get_connection por request); controllers só falam com models/services e nunca com o driver (Playbook P-08).

### [HIGH] Configuração insegura (AP-11)
File: app.py:8, 9, 88, controllers.py:286-288, database.py:5
Description: DEBUG = True e app.run(host="0.0.0.0", port=5000, debug=True) fixos no código, CORS(app) aberto para qualquer origem, "ambiente": "producao" e db_path = "loja.db" hardcoded.
Impact: O debugger do Werkzeug fica exposto na rede (execução remota de código); ambiente, porta e banco não são configuráveis.
Recommendation: config/settings.py com FLASK_DEBUG (default false), HOST, PORT, DATABASE_PATH, CORS_ORIGINS e APP_ENV lidos de variáveis de ambiente (Playbook P-02).

### [HIGH] Validação de entrada ausente ou fraca (AP-16)
File: controllers.py:195-201, models.py:139-146, controllers.py:169-171, 153-158
Description: criar_pedido não valida os itens: "quantidade" negativa ou zero passa (total fica negativo e o estoque AUMENTA), item sem chave produto_id/quantidade ou com string dá KeyError/TypeError e 500. login chama dados.get(...) sem checar se request.get_json() é None (500). criar_usuario aceita email sem formato e senha de qualquer tamanho. Severidade elevada de MEDIUM: fluxo de dinheiro e autenticação.
Impact: Dá para gerar pedido com total negativo e inflar estoque; entrada malformada retorna 500 em vez de 400.
Recommendation: Validators dedicados (validate_pedido, validate_login, validate_usuario) que checam tipo/faixa (quantidade inteira > 0) e retornam 400 antes de chegar ao service (Playbook P-14).

### [MEDIUM] Queries N+1 (AP-13)
File: models.py:186-199, 218-231, 139-141, 154-156, 239-254, controllers.py:269-274
Description: get_pedidos_usuario e get_todos_pedidos fazem uma query de itens por pedido e mais uma de nome por item (cursor2/cursor3). criar_pedido busca cada produto duas vezes. relatorio_vendas faz 5 consultas COUNT/SUM separadas e health_check faz 4.
Impact: O número de queries cresce linearmente com pedidos × itens, e a listagem de pedidos fica lenta conforme a base cresce.
Recommendation: Um único SELECT de itens com JOIN em produtos para os pedidos carregados (agrupados em memória); relatório com uma query agregada (SUM(CASE ...)/GROUP BY status); reaproveitar os produtos lidos na validação do pedido (Playbook P-09).

### [MEDIUM] Lógica e validação duplicadas (AP-14)
File: controllers.py:28-46, 72-90, models.py:12-21, 31-40, 304-313, 79-86, 95-102, 177-200, 210-232, controllers.py:242, models.py:247-253
Description: O bloco de validação de produto foi copiado entre criar_produto e atualizar_produto; o mapeamento row→dict de produto aparece 3 vezes e o de usuário 2 vezes; a montagem de pedido+itens é idêntica em get_pedidos_usuario e get_todos_pedidos; os literais de status se repetem em controller e model.
Impact: As regras já divergiram (o update não valida nome nem categoria) e cada correção precisa ser replicada.
Recommendation: Funções únicas _row_to_produto/_row_to_usuario/_montar_pedidos no model, um validate_produto compartilhado e constantes STATUS_PEDIDO/CATEGORIAS_VALIDAS (Playbook P-07, P-14).

### [MEDIUM] Validação de entrada ausente ou fraca (AP-16)
File: controllers.py:43-50, 72-90, 239-245
Description: Em produtos, preco/estoque não têm o tipo checado ("10" < 0 lança TypeError e dá 500), e o update ignora as regras de nome e categoria do create. Em atualizar_status_pedido, dados.get sem checar None (500 com corpo vazio) e status de pedido inexistente devolve 200.
Impact: Erros 500 em vez de 400 e dados inválidos persistidos (categoria fora da lista via PUT).
Recommendation: validate_produto único (tipos numéricos, faixas, nome, categoria) para create e update; checar corpo JSON e existência do pedido antes de atualizar (Playbook P-14).

### [MEDIUM] Tratamento de erro genérico / sem handler central (AP-17)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292, app.py:77-78
Description: Os 17 handlers repetem "except Exception as e: return jsonify({"erro": str(e)}), 500"; não existe @app.errorhandler e os formatos de erro variam (com e sem "sucesso": False).
Impact: Mensagens internas (SQL, paths, tipos) vazam para o cliente; os erros reais não são logados.
Recommendation: Middleware error_handler com @app.errorhandler(Exception) que loga o stack trace e responde {"erro": "Erro interno do servidor"} 500; exceções de domínio (ValidationError/NotFound) mapeadas para 400/404; remover os try/except dos controllers (Playbook P-12).

### [MEDIUM] Responsabilidade no módulo errado (AP-18)
File: app.py:32-78, database.py:56-84
Description: O entry point declara as rotas GET /, POST /admin/reset-db e POST /admin/query com SQL inline; a função de conexão get_db() também popula o seed.
Impact: Rotas administrativas ficam fora da camada de rotas e não são encontradas por quem procura os módulos de domínio; a conexão tem efeito colateral de dados.
Recommendation: Mover as rotas para views/admin_routes.py e views/sistema_routes.py, o SQL para admin_model.py e o seed para database/seed.py chamado no create_app (Playbook P-03).

### [LOW] Magic numbers e strings (AP-19)
File: models.py:256-262, controllers.py:47-50, 52, 242, models.py:150, 247-253, app.py:35, 85, 88, controllers.py:285
Description: Faixas de desconto 10000/5000/1000 com 0.1/0.05/0.02 literais, limites de nome 2/200, listas de categorias/status inline, 'pendente' solto no INSERT, porta 5000 e versão "1.0.0" repetidas.
Impact: A regra fica opaca e mudar um valor exige caçar todos os literais.
Recommendation: Constantes nomeadas (FAIXAS_DESCONTO, NOME_MIN/NOME_MAX, STATUS_PEDIDO, CATEGORIAS_VALIDAS, APP_VERSION) em módulo de domínio/config (Playbook P-15).

### [LOW] Nomenclatura ruim (AP-20)
File: controllers.py:14, 56, 64, 98, 136, 160, models.py:24, 54, 65, 89, 187, 191, 196, 219, 223, 228
Description: O parâmetro/variável "id" sombreia o builtin; "cursor2"/"cursor3"/"prod" são genéricos; a nomenclatura mistura inglês e português (get_todos_produtos, get_produto_por_id).
Impact: Leitura mais difícil e risco de bugs sutis com o builtin id.
Recommendation: Renomear internamente (produto_id, usuario_id, itens_rows), mantendo os nomes de rota (<int:id>) e as chaves do JSON (Playbook P-15).

### [LOW] print como logging (AP-21)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 219, 248, 250, app.py:56, 83-86
Description: Eventos e erros saem via print("ERRO: " + str(e)), print("Login bem-sucedido: " + email) etc., sem nível e com e-mail de usuário no stdout.
Impact: Sem nível nem filtro de log; dados pessoais vão para o stdout.
Recommendation: logging.getLogger(__name__) com níveis info/warning/exception, sem registrar e-mail completo (Playbook P-16).

### [LOW] Código, import ou dependência morta (AP-22)
File: database.py:2, models.py:2, controllers.py:268
Description: "import os" (database.py) e "import sqlite3" (models.py) nunca são usados; cursor.execute("SELECT 1") em health_check descarta o resultado.
Impact: Ruído e falsa impressão de dependência.
Recommendation: Remover os imports e a query redundante (Playbook P-16).

## Deprecated APIs
None detected — verified against catalog AP-15 (sem datetime.utcnow/utcfromtimestamp, sqlite3.connect sem detect_types e sem datetime como parâmetro, sem before_first_request/json_encoder/safe_str_cmp/pkg_resources)

## Endpoint Inventory
GET /produtos — app.py:11
GET /produtos/busca — app.py:12
GET /produtos/<int:id> — app.py:13
POST /produtos — app.py:14
PUT /produtos/<int:id> — app.py:15
DELETE /produtos/<int:id> — app.py:16
GET /usuarios — app.py:18
GET /usuarios/<int:id> — app.py:19
POST /usuarios — app.py:20
POST /login — app.py:21
POST /pedidos — app.py:23
GET /pedidos — app.py:24
GET /pedidos/usuario/<int:usuario_id> — app.py:25
PUT /pedidos/<int:pedido_id>/status — app.py:26
GET /relatorios/vendas — app.py:28
GET /health — app.py:30
GET / — app.py:32
POST /admin/reset-db — app.py:47
POST /admin/query — app.py:59

================================
Total: 21 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
