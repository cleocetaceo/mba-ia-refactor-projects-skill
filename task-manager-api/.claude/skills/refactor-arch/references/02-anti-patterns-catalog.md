# 02 — Catálogo de Anti-Patterns (Fase 2)

Cada anti-pattern tem um ID, uma severidade padrão, sinais de detecção concretos e o padrão do playbook (`05-refactoring-playbook.md`) que o corrige.

## Escala de severidade

| Severidade | Critério (MVC + SOLID) |
|---|---|
| **CRITICAL** | Falha grave de segurança ou arquitetura: expõe dados sensíveis, permite execução arbitrária ou viola completamente a separação de responsabilidades. |
| **HIGH** | Forte violação de MVC/SOLID que dificulta muito manutenção e testes: regra de negócio no controller/rota, acoplamento sem injeção de dependência, estado global mutável, escrita não atômica. |
| **MEDIUM** | Padronização, duplicação, performance moderada (N+1), validação ausente, middleware inadequado, APIs deprecated. |
| **LOW** | Legibilidade: nomes ruins, magic numbers, logging com `print`, código morto. |

**Regras de ajuste:**
- Suba um nível quando o problema estiver num fluxo de dinheiro, autenticação ou dados pessoais (ex.: N+1 no relatório financeiro continua MEDIUM, mas validação ausente no checkout de pagamento sobe para HIGH).
- Desça um nível quando o código afetado estiver morto (nunca chamado). Registre isso na descrição.
- Nunca reporte o mesmo trecho em dois anti-patterns de mesma natureza. Ex.: secret hardcoded que também vaza no `/health` gera AP-02 (hardcoded) e AP-06 (exposição), porque são problemas diferentes.

## Índice

| ID | Anti-pattern | Severidade | Playbook |
|---|---|---|---|
| AP-01 | SQL Injection | CRITICAL | P-01 |
| AP-02 | Credenciais e secrets hardcoded | CRITICAL | P-02 |
| AP-03 | God Class / God Module | CRITICAL | P-03 |
| AP-04 | Armazenamento inseguro de senha / criptografia fraca | CRITICAL | P-04 |
| AP-05 | Endpoint perigoso sem autenticação | CRITICAL | P-05 |
| AP-06 | Exposição de dados sensíveis | CRITICAL | P-06 |
| AP-07 | Regra de negócio na rota/controller (Fat Controller) | HIGH | P-07 |
| AP-08 | Estado global mutável | HIGH | P-08 |
| AP-09 | Acoplamento forte sem injeção de dependência | HIGH | P-08 |
| AP-10 | Escrita multi-etapa sem transação | HIGH | P-10 |
| AP-11 | Configuração insegura (debug em produção, bind aberto) | HIGH | P-02 |
| AP-12 | Callback hell / fluxo assíncrono aninhado | HIGH | P-11 |
| AP-13 | Queries N+1 | MEDIUM | P-09 |
| AP-14 | Lógica e validação duplicadas | MEDIUM | P-07, P-14 |
| AP-15 | Uso de APIs deprecated | MEDIUM | P-13 |
| AP-16 | Validação de entrada ausente ou fraca | MEDIUM | P-14 |
| AP-17 | Tratamento de erro genérico / sem handler central | MEDIUM | P-12 |
| AP-18 | Responsabilidade no módulo errado | MEDIUM | P-03 |
| AP-19 | Magic numbers e strings | LOW | P-15 |
| AP-20 | Nomenclatura ruim | LOW | P-15 |
| AP-21 | `print`/`console.log` como logging | LOW | P-16 |
| AP-22 | Código, import ou dependência morta | LOW | P-16 |

---

## CRITICAL

### AP-01 — SQL Injection
**Sinais de detecção:**
- SQL montado com concatenação: `"... WHERE id = " + str(id)`, `"' + nome + '"`.
- f-string ou `%`/`.format()` dentro de SQL: `f"SELECT ... {termo}"`, `"... '%s'" % valor`.
- Template literal com interpolação em SQL (JS): `` `SELECT * FROM users WHERE id = ${id}` ``.
- `cursor.execute(<variável>)` cujo valor vem do request.
- `LIKE '%" + termo + "%'` em buscas.

**Não é SQL Injection:** placeholders (`?`, `%s`, `:nome`, `$1`) com parâmetros separados; métodos de ORM (`filter_by`, `.like()` do SQLAlchemy com parâmetro).

**Impacto:** leitura, alteração ou destruição de qualquer dado; bypass de login (`' OR '1'='1`).

### AP-02 — Credenciais e secrets hardcoded
**Sinais de detecção:**
- Atribuições literais a chaves sensíveis: `SECRET_KEY = "..."`, `password = '...'`, `dbPass`, `apiKey`, `paymentGatewayKey`, `token`, `smtp_password`, `email_password`.
- Prefixos de chaves reais: `pk_live_`, `sk_live_`, `AKIA`, `ghp_`, `xox`.
- Objetos de config com credenciais literais (`const config = { dbPass: "..." }`).
- URIs de banco com usuário:senha no código.

**Não reportar:** seeds de desenvolvimento com usuários de exemplo (avalie como AP-04 se a senha ficar em texto puro no banco).

**Impacto:** qualquer pessoa com acesso ao repositório obtém as credenciais; rotação exige deploy.

### AP-03 — God Class / God Module
**Sinais de detecção:**
- Uma classe ou arquivo com responsabilidades de **duas ou mais camadas** (conexão/SQL + rotas HTTP + regra de negócio).
- Um arquivo de models/serviço que atende **três ou mais domínios** (produtos, usuários, pedidos, relatórios).
- Classe com nome genérico (`AppManager`, `Manager`, `Helper`, `Utils`) que cria o banco, define rotas e processa pagamentos.
- Arquivo acima de ~300 linhas misturando domínios, ou método acima de ~50 linhas com vários níveis de aninhamento.

**Impacto:** impossível testar em isolamento; qualquer mudança arrisca regressão em outro domínio.

### AP-04 — Armazenamento inseguro de senha / criptografia fraca
**Sinais de detecção:**
- Senha gravada e comparada em texto puro: `INSERT ... senha` com o valor recebido; `WHERE senha = '...'`.
- Hash rápido sem salt: `hashlib.md5(`, `hashlib.sha1(`, `sha256(pwd)` sem salt/iterações; `crypto.createHash('md5')`.
- "Criptografia" caseira: base64, loops de concatenação, `substring`, XOR (ex.: função `badCrypto`).
- Senha padrão quando o usuário não envia (`pwd || "123456"`).

**Impacto:** vazamento do banco expõe todas as senhas; rainbow tables quebram MD5 em segundos.

### AP-05 — Endpoint perigoso sem autenticação
**Sinais de detecção:**
- Rotas que executam SQL recebido do cliente (`/admin/query` com `cursor.execute(dados["sql"])`).
- Rotas destrutivas sem verificação de credencial: reset de banco, `DELETE` de usuários, apagar tabelas.
- Relatórios administrativos/financeiros (`/admin/...`, `/reports/financial`) acessíveis a qualquer cliente.
- Login que devolve token falso (`'fake-jwt-token-' + id`) e nenhuma rota que o valide.
- Cliente que define o próprio papel (`role: "admin"`) sem autorização.

**Impacto:** controle total do sistema ou escalada de privilégio por qualquer cliente anônimo.

### AP-06 — Exposição de dados sensíveis
**Sinais de detecção:**
- Serialização que inclui senha/hash: `"senha": row["senha"]`, `'password': self.password` em `to_dict()`.
- Endpoint de health/debug que devolve `secret_key`, `db_path`, `debug`, variáveis de ambiente.
- Log de cartão de crédito, token ou chave de API: `console.log(\`Processando cartão ${cc} na chave ${key}\`)`.
- Mensagens de exceção internas devolvidas ao cliente (`return {"erro": str(e)}`) — reporte em AP-17 se for o único problema.

**Impacto:** vazamento de credenciais e dados de pagamento; violação de LGPD/PCI-DSS.

---

## HIGH

### AP-07 — Regra de negócio na rota/controller (Fat Controller)
**Sinais de detecção:**
- Handler HTTP que, além de ler o request e responder, calcula valores, aplica regras de status, faz queries e formata dados (ex.: rota de 50+ linhas).
- Efeitos colaterais de domínio dentro da rota: envio de e-mail/SMS/push, cálculo de desconto, regra de atraso (`overdue`).
- Camada de serviço existente mas não usada pelas rotas.

**Impacto:** regra impossível de reutilizar e testar sem HTTP; duplicação entre rotas.

### AP-08 — Estado global mutável
**Sinais de detecção:**
- Variáveis de módulo reatribuídas em runtime: `global db_connection`, `let globalCache = {}`, `let totalRevenue = 0`.
- Conexão de banco singleton compartilhada entre threads (`sqlite3.connect(..., check_same_thread=False)` em variável global).
- Listas/dicts de módulo usados como armazenamento (`self.notifications = []` num serviço singleton).

**Impacto:** condições de corrida, vazamento de dados entre requisições, testes que interferem entre si.

### AP-09 — Acoplamento forte sem injeção de dependência
**Sinais de detecção:**
- Classes que instanciam suas dependências concretas internamente (`this.db = new sqlite3.Database(...)` no construtor, `NotificationService()` dentro da rota).
- Funções que chamam `get_db()` global em vez de receber a conexão/repositório.
- Controllers importando o driver de banco diretamente.

**Impacto:** impossível substituir dependências em testes; troca de infraestrutura exige editar regra de negócio.

### AP-10 — Escrita multi-etapa sem transação
**Sinais de detecção:**
- Sequência de `INSERT`/`UPDATE` relacionados sem `BEGIN/COMMIT/ROLLBACK` (pedido + itens + baixa de estoque; matrícula + pagamento + auditoria).
- `return` de erro no meio de um loop de escrita, deixando registros parciais.
- `DELETE` do pai sem tratar filhos (registros órfãos).

**Impacto:** dados inconsistentes em falhas parciais (pagamento sem matrícula, estoque baixado sem pedido).

### AP-11 — Configuração insegura
**Sinais de detecção:**
- `debug=True`, `app.config["DEBUG"] = True`, `app.run(debug=True)` fixos no código.
- Bind em `0.0.0.0` junto com debug ligado (debugger Werkzeug exposto na rede).
- CORS liberado para qualquer origem em API com credenciais, quando combinado com outros problemas.
- Valores de ambiente fixos ("ambiente": "producao") no código.

**Impacto:** execução remota de código pelo debugger; comportamento de produção não configurável.

### AP-12 — Callback hell / fluxo assíncrono aninhado
**Sinais de detecção:**
- Três ou mais níveis de callbacks aninhados (`db.get(..., (err, x) => { db.run(..., function(err) { ... }) })`).
- Contadores manuais para saber quando callbacks paralelos terminaram (`pending--; if (pending === 0) res.json(...)`).
- Erros de callback ignorados (`(err) => { res.send(...) }` sem checar `err`).

**Impacto:** fluxo ilegível, respostas duplicadas ou nunca enviadas, erros engolidos.

---

## MEDIUM

### AP-13 — Queries N+1
**Sinais de detecção:**
- Query dentro de loop sobre resultado de outra query: `for row in rows: cursor.execute("SELECT ... WHERE id = " + row["x"])`.
- ORM: acesso a relacionamento ou `Model.query.get(id)` dentro de loop sobre uma lista.
- Contagens por item em loop (`Task.query.filter_by(user_id=u.id).count()` para cada usuário).
- Várias queries `COUNT(*)` separadas que poderiam ser um único `GROUP BY`.

**Impacto:** latência cresce linearmente com o volume de dados.

### AP-14 — Lógica e validação duplicadas
**Sinais de detecção:**
- O mesmo bloco de validação em create e update (campos obrigatórios, faixas de valores).
- A mesma regra de negócio repetida em vários handlers (ex.: cálculo de `overdue` em 5 lugares) enquanto existe um método equivalente no model.
- Mapeamento `row → dict` copiado em várias funções.
- Listas de valores válidos (status, categorias, roles) repetidas como literais.

**Impacto:** regras divergem com o tempo; correções precisam ser replicadas.

### AP-15 — Uso de APIs deprecated
Procure as APIs abaixo e recomende o equivalente moderno. Cite a versão em que a API foi depreciada quando souber.

| Stack | API deprecated | Substituto moderno |
|---|---|---|
| Python 3.12+ | `datetime.utcnow()` | `datetime.now(timezone.utc)` (ou `datetime.now(UTC)`) |
| Python 3.12+ | `datetime.utcfromtimestamp(ts)` | `datetime.fromtimestamp(ts, tz=timezone.utc)` |
| Python 3.12+ | adaptadores padrão de `datetime` do `sqlite3` | registrar adaptadores explícitos ou gravar ISO strings |
| SQLAlchemy 2.0 / Flask-SQLAlchemy 3 | `Model.query.get(id)` / `session.query(M).get(id)` | `db.session.get(Model, id)` |
| SQLAlchemy 2.0 | `engine.execute(...)`, `Model.query` como estilo principal | `db.session.execute(db.select(...))` |
| Flask 2.3+ | `@app.before_first_request` | lógica no `create_app()` / `with app.app_context()` |
| Flask 2.3+ | `flask.json.JSONEncoder` / `app.json_encoder` | `app.json` provider (`DefaultJSONProvider`) |
| Werkzeug | `werkzeug.contrib.*`, `safe_str_cmp` | `hmac.compare_digest` |
| setuptools | `pkg_resources` | `importlib.metadata` / `importlib.resources` |
| Node.js | `new Buffer(x)` | `Buffer.from(x)` / `Buffer.alloc(n)` |
| Node.js | `crypto.createCipher` / `createDecipher` | `crypto.createCipheriv` / `createDecipheriv` |
| Node.js | `url.parse()` | `new URL()` (WHATWG) |
| Node.js | `fs.exists()`, `util.isArray()` etc. | `fs.existsSync`/`fs.promises.access`, `Array.isArray()` |
| Express 4 | `res.send(status, body)`, `res.json(status, obj)`, `req.param()` | `res.status(s).send(body)`, `req.params`/`req.query`/`req.body` |
| Express 4 | pacote `body-parser` separado | `express.json()` / `express.urlencoded()` |
| npm | pacote `request` | `fetch` nativo (Node 18+) ou `undici` |

Também conte como AP-15 o uso de algoritmos obsoletos para a finalidade em questão (MD5/SHA1 para senha), mas reporte a falha de segurança principal em AP-04 e cite AP-15 apenas como complemento.

Se nenhuma API deprecated for encontrada, declare isso explicitamente no relatório.

### AP-16 — Validação de entrada ausente ou fraca
**Sinais de detecção:**
- Campos do body usados sem verificação de tipo/faixa (`if priority < 1` com valor que pode ser string → `TypeError` 500).
- `request.get_json()` usado sem checar `None` antes de `.get(...)`.
- Formatos não validados (e-mail, cartão, datas) ou regras fracas (senha mínima de 4 caracteres).
- Update que não aplica as mesmas regras do create.

**Impacto:** erros 500 em vez de 400, dados inválidos persistidos.

### AP-17 — Tratamento de erro genérico / sem handler central
**Sinais de detecção:**
- `except:` ou `except Exception` que engole o erro, ou `catch` vazio.
- `try/except` idêntico repetido em todos os handlers devolvendo `str(e)` ao cliente.
- Ausência de `@app.errorhandler` / middleware de erro (`app.use((err, req, res, next) => ...)`).
- Respostas de erro com formatos diferentes entre rotas.

**Impacto:** detalhes internos vazam ao cliente; erros reais ficam invisíveis.

### AP-18 — Responsabilidade no módulo errado
**Sinais de detecção:**
- Rotas de um domínio declaradas no arquivo de outro (CRUD de categorias dentro de `report_routes.py`).
- Rotas administrativas ou de negócio declaradas no entry point (`app.py`).
- Helpers de domínio em `utils/` genérico.

**Impacto:** dificulta encontrar código e viola coesão por domínio.

---

## LOW

### AP-19 — Magic numbers e strings
**Sinais de detecção:** limites e percentuais literais em regra de negócio (`if faturamento > 10000: desconto = faturamento * 0.1`), status como string solta (`'done'`, `'PAID'`), portas e tamanhos literais repetidos.

### AP-20 — Nomenclatura ruim
**Sinais de detecção:** variáveis de uma letra ou abreviações crípticas (`u`, `e`, `p`, `cc`, `cid`), campos de API abreviados (`usr`, `eml`, `pwd`, `c_id`), nomes genéricos (`data`, `result`, `AppManager`), mistura de idiomas no mesmo módulo.

> Ao corrigir nomes de campos de API, mantenha os nomes públicos do contrato e renomeie apenas as variáveis internas.

### AP-21 — `print`/`console.log` como logging
**Sinais de detecção:** `print(...)`/`console.log(...)` para eventos de negócio e erros em código de produção; ausência de níveis de log.

### AP-22 — Código, import ou dependência morta
**Sinais de detecção:** imports não usados (`import os, sys, json` sem uso), funções/módulos nunca chamados, dependências no manifesto não importadas, variáveis exportadas e nunca lidas.

---

## Checklist de varredura por arquivo

Para cada arquivo-fonte, verifique na ordem:

1. Strings SQL e chamadas `execute`/`run`/`get`/`all` → AP-01, AP-13
2. Literais de secrets e config → AP-02, AP-11
3. Senhas: escrita, comparação, hash e serialização → AP-04, AP-06
4. Rotas: autenticação, tamanho do handler, regra de negócio, validação → AP-05, AP-07, AP-16, AP-18
5. Variáveis globais e instanciação de dependências → AP-08, AP-09
6. Sequências de escrita → AP-10
7. Callbacks e tratamento de erro → AP-12, AP-17
8. APIs da tabela de deprecated → AP-15
9. Duplicação entre arquivos → AP-14
10. Legibilidade (números, nomes, prints, imports) → AP-19 a AP-22
