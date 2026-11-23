# 05 — Playbook de Refatoração (Fase 3)

Transformações concretas para cada anti-pattern do catálogo. Cada padrão traz o código **antes** e **depois**. Adapte nomes e caminhos ao projeto; preserve o contrato HTTP (ver `04-mvc-architecture-guidelines.md`).

| Padrão | Corrige | Título |
|---|---|---|
| P-01 | AP-01 | Queries parametrizadas |
| P-02 | AP-02, AP-11 | Extrair configuração para ambiente |
| P-03 | AP-03, AP-18 | Quebrar God Class em camadas MVC |
| P-04 | AP-04 | Hash de senha forte com migração |
| P-05 | AP-05 | Proteger endpoints perigosos |
| P-06 | AP-06 | Serialização segura e logs sem dados sensíveis |
| P-07 | AP-07, AP-14 | Mover regra de negócio da rota para o controller |
| P-08 | AP-08, AP-09 | Eliminar estado global e injetar dependências |
| P-09 | AP-13 | Eliminar N+1 com JOIN, eager loading ou agregação |
| P-10 | AP-10 | Transação em escrita multi-etapa |
| P-11 | AP-12 | Callbacks para async/await |
| P-12 | AP-17 | Handler central de erros |
| P-13 | AP-15 | Substituir APIs deprecated |
| P-14 | AP-14, AP-16 | Validação centralizada |
| P-15 | AP-19, AP-20 | Constantes nomeadas e nomes claros |
| P-16 | AP-21, AP-22 | Logging estruturado e remoção de código morto |

---

## P-01 — Queries parametrizadas

**Python (sqlite3) — antes**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
query += " AND (nome LIKE '%" + termo + "%')"
```
**Depois**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))

clauses, params = ["1=1"], []
if termo:
    clauses.append("(nome LIKE ? OR descricao LIKE ?)")
    params += [f"%{termo}%", f"%{termo}%"]
cursor.execute(f"SELECT * FROM produtos WHERE {' AND '.join(clauses)}", params)
```
**Node (sqlite3) — antes / depois**
```js
db.all(`SELECT * FROM users WHERE id = ${id}`);          // antes
db.all('SELECT * FROM users WHERE id = ?', [id]);        // depois
```
Regra: só fragmentos fixos escritos pelo desenvolvedor podem ser concatenados; valores sempre vão como parâmetro.

## P-02 — Extrair configuração para ambiente

**Antes**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.run(host="0.0.0.0", port=5000, debug=True)
```
**Depois — `src/config/settings.py`**
```python
import os
import secrets

def _bool(value, default=False):
    return default if value is None else value.strip().lower() in ("1", "true", "yes", "on")

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _bool(os.environ.get("FLASK_DEBUG"))
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")
```
```python
# app.py (entry point)
from src.app import create_app
from src.config.settings import Settings

app = create_app()

if __name__ == "__main__":
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
```
**Node — antes / depois**
```js
// antes (utils.js)
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_123", port: 3000 };
```
```js
// depois (src/config/index.js)
module.exports = Object.freeze({
  port: Number(process.env.PORT) || 3000,
  databasePath: process.env.DATABASE_PATH || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  adminToken: process.env.ADMIN_TOKEN || '',
});
```
Crie `.env.example` listando as variáveis, sem valores reais.

## P-03 — Quebrar God Class em camadas MVC

**Antes** — uma classe cria o banco, define rotas e processa o caso de uso:
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  setupRoutes(app) {
    app.post('/api/checkout', (req, res) => { /* SQL + pagamento + auditoria */ });
  }
}
```
**Depois** — cada responsabilidade na sua camada:
```js
// src/models/course.model.js
module.exports = (db) => ({
  findActiveById: (id) => db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]),
});

// src/controllers/checkout.controller.js
module.exports = ({ courseModel, userModel, enrollmentModel, paymentService }) => ({
  async checkout(input) { /* regra do caso de uso, sem req/res */ },
});

// src/routes/checkout.routes.js
module.exports = (controller) => {
  const router = require('express').Router();
  router.post('/checkout', async (req, res, next) => {
    try { res.status(200).json(await controller.checkout(req.body)); } catch (err) { next(err); }
  });
  return router;
};
```
**Python** — divida o `models.py` gigante por domínio (`produto_model.py`, `usuario_model.py`, `pedido_model.py`) e o `controllers.py` em controllers por domínio. As rotas vão para Blueprints em `views/`.

**AP-18 (módulo errado):** mova as rotas para o arquivo do domínio correto sem mudar a URL:
```python
# antes: routes/report_routes.py contém @report_bp.route('/categories')
# depois: routes/category_routes.py
category_bp = Blueprint('categories', __name__)

@category_bp.route('/categories', methods=['GET'])
def list_categories():
    return jsonify(category_controller.list_categories()), 200
```

## P-04 — Hash de senha forte com migração

**Antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
cursor.execute("INSERT INTO usuarios (..., senha) VALUES (..., '" + senha + "')")   # texto puro
```
**Depois (Flask — `werkzeug` já vem com o Flask)**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, raw):
    self.password = generate_password_hash(raw)

def check_password(self, raw):
    return check_password_hash(self.password, raw)
```
**Node — antes / depois**
```js
function badCrypto(pwd) { /* base64 em loop */ }                    // antes
```
```js
// src/services/password.service.js
const crypto = require('node:crypto');

function hashPassword(plain) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(plain, salt, 64).toString('hex');
  return `scrypt$${salt}$${hash}`;
}

function verifyPassword(plain, stored) {
  const [, salt, hash] = String(stored).split('$');
  if (!salt || !hash) return false;
  const candidate = crypto.scryptSync(plain, salt, 64);
  return crypto.timingSafeEqual(candidate, Buffer.from(hash, 'hex'));
}
```
**Migração:** o seed passa a gravar senhas com hash (as mesmas senhas de exemplo continuam funcionando no login). Se o banco é persistente e já contém hashes antigos, aceite o formato legado na verificação e regrave com hash forte após login bem-sucedido. Nunca use senha padrão (`pwd || "123456"`): campo obrigatório ausente → 400.

## P-05 — Proteger endpoints perigosos

**Antes**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json()["sql"])
```
**Depois — `src/middlewares/auth.py`**
```python
import hmac
from functools import wraps
from flask import current_app, request, jsonify

def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN")
        if not expected:
            return jsonify({"erro": "Endpoint administrativo desabilitado"}), 403
        provided = request.headers.get("X-Admin-Token", "")
        if not hmac.compare_digest(provided, expected):
            return jsonify({"erro": "Não autorizado"}), 401
        return view(*args, **kwargs)
    return wrapper
```
```python
@admin_bp.route("/admin/query", methods=["POST"])
@require_admin
def executar_query():
    return jsonify(admin_controller.executar_query(request.get_json(silent=True) or {})), 200
```
```python
import re

_LEITURA = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)

def executar_query(dados):
    sql = dados.get("sql", "") if isinstance(dados, dict) else ""
    if not isinstance(sql, str) or not sql.strip():
        raise ValidationError("Query não informada")
    # Uma sentença, sem ';' extra. WITH só vale quando a sentença é um SELECT.
    corpo = sql.strip().rstrip(";").strip()
    if ";" in corpo or not _LEITURA.match(corpo) or re.search(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH)\b", corpo, re.IGNORECASE):
        raise ValidationError("Apenas uma sentença SELECT é permitida")
    db = get_db()
    return {"dados": admin_model.consultar(db, corpo), "sucesso": True}
```
O token de admin não autoriza escrita. `SELECT` com token devolve o mesmo JSON de sucesso de antes; qualquer outra sentença responde 400.
**Node**
```js
// src/middlewares/adminAuth.js
const crypto = require('node:crypto');

module.exports = (adminToken) => (req, res, next) => {
  if (!adminToken) return res.status(403).send('Endpoint administrativo desabilitado');
  const provided = Buffer.from(req.get('X-Admin-Token') || '');
  const expected = Buffer.from(adminToken);
  if (provided.length !== expected.length || !crypto.timingSafeEqual(provided, expected)) {
    return res.status(401).send('Não autorizado');
  }
  next();
};
```
**Privilégio enviado pelo cliente:** ignore `role`/`tipo` do body, a menos que a requisição tenha credencial de admin válida.

## P-06 — Serialização segura e logs sem dados sensíveis

**Antes**
```python
return {"id": row["id"], "email": row["email"], "senha": row["senha"]}
# health
return jsonify({"status": "ok", "secret_key": app.config["SECRET_KEY"], "debug": True})
```
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```
**Depois**
```python
PUBLIC_USER_FIELDS = ("id", "nome", "email", "tipo", "criado_em")

def to_public_dict(row):
    return {field: row[field] for field in PUBLIC_USER_FIELDS}

return jsonify({"status": "ok", "database": "connected", "counts": counts, "versao": "1.0.0"})
```
```js
const maskCard = (card) => `**** **** **** ${String(card).slice(-4)}`;
logger.info(`Processando pagamento do cartão ${maskCard(card)}`);
```
Use allowlist de campos públicos, nunca denylist.

## P-07 — Mover regra de negócio da rota para o controller

**Antes**
```python
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    result = []
    for t in tasks:
        data = {...}
        if t.due_date and t.due_date < datetime.utcnow() and t.status not in ('done', 'cancelled'):
            data['overdue'] = True
        user = User.query.get(t.user_id)
        ...
    return jsonify(result), 200
```
**Depois**
```python
# controllers/task_controller.py
def list_tasks():
    tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
    return [task.to_dict(include_relations=True) for task in tasks]

# models/task.py
def to_dict(self, include_relations=False):
    data = {...}
    data["overdue"] = self.is_overdue()
    if include_relations:
        data["user_name"] = self.user.name if self.user else None
        data["category_name"] = self.category.name if self.category else None
    return data

# routes/task_routes.py
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(task_controller.list_tasks()), 200
```
Efeitos colaterais (e-mail, SMS, push) saem da rota e vão para um service chamado pelo controller:
```python
# antes (na rota): print("ENVIANDO EMAIL: Pedido ...")
# depois (no controller):
notification_service.pedido_criado(pedido_id, usuario_id)
```

## P-08 — Eliminar estado global e injetar dependências

**Python — antes**
```python
db_connection = None

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
    return db_connection
```
**Depois — conexão por request**
```python
import sqlite3
from flask import current_app, g

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_schema_and_seed(get_db())
```
**Node — antes / depois**
```js
let globalCache = {};                                     // antes: estado de módulo mutável
class AppManager { constructor() { this.db = new sqlite3.Database(':memory:'); } }
```
```js
// depois: composition root cria e injeta
const db = createConnection(config.databasePath);
const cache = createCache();                              // instância encapsulada, injetada
const checkoutController = createCheckoutController({ courseModel: courseModel(db), cache });
app.use('/api', checkoutRoutes(checkoutController));
```

## P-09 — Eliminar N+1 com JOIN, eager loading ou agregação

**SQL cru — antes**
```python
for pedido in pedidos:
    itens = cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(pedido["id"]))
    for item in itens:
        prod = cursor.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
**Depois — uma query com JOIN e agrupamento em memória**
```python
rows = db.execute("""
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    ORDER BY p.id
""").fetchall()
pedidos = {}
for r in rows:
    pedido = pedidos.setdefault(r["id"], {"id": r["id"], "usuario_id": r["usuario_id"], "status": r["status"],
                                          "total": r["total"], "criado_em": r["criado_em"], "itens": []})
    if r["produto_id"] is not None:
        pedido["itens"].append({"produto_id": r["produto_id"],
                                "produto_nome": r["produto_nome"] or "Desconhecido",
                                "quantidade": r["quantidade"], "preco_unitario": r["preco_unitario"]})
return list(pedidos.values())
```
**ORM — antes / depois**
```python
for t in Task.query.all():
    user = User.query.get(t.user_id)                       # antes: 1 query por task
```
```python
from sqlalchemy.orm import joinedload
Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()   # depois
```
**Contagens — antes / depois**
```python
pending = Task.query.filter_by(status='pending').count()   # antes: uma query por status
done = Task.query.filter_by(status='done').count()
```
```python
from sqlalchemy import func
counts = dict(db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all())
pending, done = counts.get('pending', 0), counts.get('done', 0)
```

## P-10 — Transação em escrita multi-etapa

**Antes**
```python
cursor.execute("INSERT INTO pedidos ...")
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ...")
db.commit()
```
**Depois (sqlite3)**
```python
try:
    pedido_id = pedido_model.inserir(db, usuario_id, total)
    for item in itens:
        item_model.inserir(db, pedido_id, item)
        produto_model.baixar_estoque(db, item["produto_id"], item["quantidade"])
    db.commit()
except Exception:
    db.rollback()
    raise
```
**Node (helpers com Promise)**
```js
await db.run('BEGIN');
try {
  const enrollmentId = await enrollmentModel.create(userId, courseId);
  await paymentModel.create(enrollmentId, course.price, status);
  await auditModel.log(`Checkout curso ${courseId} por ${userId}`);
  await db.run('COMMIT');
  return enrollmentId;
} catch (err) {
  await db.run('ROLLBACK');
  throw err;
}
```
**Exclusão com filhos:** remova ou trate registros dependentes na mesma transação (ou use `ON DELETE CASCADE`), mantendo a mesma resposta do endpoint.

## P-11 — Callbacks para async/await

**Antes**
```js
db.get('SELECT * FROM courses WHERE id = ?', [cid], (err, course) => {
  db.get('SELECT id FROM users WHERE email = ?', [email], (err, user) => {
    db.run('INSERT ...', [], function (err) { /* ... */ });
  });
});
```
**Depois — `src/database/connection.js`**
```js
const sqlite3 = require('sqlite3');

function createConnection(filename) {
  const db = new sqlite3.Database(filename);
  return {
    run: (sql, params = []) => new Promise((resolve, reject) => {
      db.run(sql, params, function (err) { err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes }); });
    }),
    get: (sql, params = []) => new Promise((resolve, reject) => {
      db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    }),
    all: (sql, params = []) => new Promise((resolve, reject) => {
      db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    }),
    exec: (sql) => new Promise((resolve, reject) => db.exec(sql, (err) => (err ? reject(err) : resolve()))),
  };
}
```
```js
const course = await courseModel.findActiveById(courseId);
if (!course) throw new NotFoundError('Curso não encontrado');
const user = await userModel.findByEmail(email);
```
Se o boot depende do schema pronto, aguarde a inicialização (`await initSchema(db)`) antes do `app.listen`.

## P-12 — Handler central de erros

**Antes**
```python
def listar_produtos():
    try:
        ...
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```
**Depois — `src/middlewares/error_handler.py`**
```python
import logging
from flask import jsonify

logger = logging.getLogger(__name__)

class AppError(Exception):
    status_code = 400
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code

class NotFoundError(AppError):
    status_code = 404

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code

    @app.errorhandler(404)
    def handle_404(_err):
        return jsonify({"erro": "Recurso não encontrado"}), 404

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro inesperado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
```
**Node**
```js
// src/middlewares/errorHandler.js
module.exports = (logger) => (err, req, res, next) => {
  const status = err.statusCode || 500;
  if (status >= 500) logger.error(err);
  res.status(status).send(status >= 500 ? 'Erro interno' : err.message);
};
// registrado por último: app.use(errorHandler(logger));
```
Mantenha o formato de corpo que a API já usava (chave `erro`/`error`, texto puro etc.).

## P-13 — Substituir APIs deprecated

```python
# antes
from datetime import datetime
created_at = db.Column(db.DateTime, default=datetime.utcnow)
task = Task.query.get(task_id)
```
```python
# depois
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)   # naive UTC, compatível com valores já gravados

created_at = db.Column(db.DateTime, default=utcnow)
task = db.session.get(Task, task_id)
```
```js
// antes
const buf = new Buffer(text);
res.send(404, 'Not found');
// depois
const buf = Buffer.from(text);
res.status(404).send('Not found');
```
Ao trocar `utcnow()` por datetimes com fuso, mantenha a comparação consistente com os valores já armazenados (naive vs aware), para não gerar `TypeError` em comparações.

## P-14 — Validação centralizada

**Antes** — mesmas checagens copiadas em create e update, quebrando com tipos inesperados:
```python
if priority < 1 or priority > 5:     # TypeError se priority vier como string
    return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400
```
**Depois**
```python
# controllers/validators.py
VALID_STATUSES = ("pending", "in_progress", "done", "cancelled")
MIN_PRIORITY, MAX_PRIORITY = 1, 5

def validate_priority(value):
    try:
        priority = int(value)
    except (TypeError, ValueError):
        raise ValidationError("Prioridade deve ser entre 1 e 5")
    if not MIN_PRIORITY <= priority <= MAX_PRIORITY:
        raise ValidationError("Prioridade deve ser entre 1 e 5")
    return priority

def validate_product_payload(data, partial=False):
    """Uma única função usada por criar e atualizar."""
```
Mantenha as mesmas mensagens de erro e os mesmos status (400/404/409) que a API já devolvia.

## P-15 — Constantes nomeadas e nomes claros

**Antes**
```python
if faturamento > 10000:
    desconto = faturamento * 0.1
elif faturamento > 5000:
    desconto = faturamento * 0.05
```
```js
let u = req.body.usr; let e = req.body.eml; let cc = req.body.card;
```
**Depois**
```python
DISCOUNT_TIERS = ((10000, 0.10), (5000, 0.05), (1000, 0.02))   # (faturamento mínimo, percentual)

def calcular_desconto(faturamento):
    for minimo, percentual in DISCOUNT_TIERS:
        if faturamento > minimo:
            return faturamento * percentual
    return 0
```
```js
const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;  // contrato preservado
```

## P-16 — Logging estruturado e remoção de código morto

**Antes**
```python
import os, sys, json, time      # não usados
print("Produto criado com ID: " + str(id))
```
```js
console.log(`[LOG] Salvando no cache: ${key}`);
```
**Depois**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Produto criado com ID %s", produto_id)
```
```js
// src/utils/logger.js
module.exports = {
  info: (msg) => console.log(`[INFO] ${new Date().toISOString()} ${msg}`),
  error: (err) => console.error(`[ERROR] ${new Date().toISOString()}`, err),
};
```
Remova imports, funções, variáveis exportadas e módulos sem uso. Dependências do manifesto que ficaram sem uso podem ser removidas; registre isso no resumo.

---

## Ordem recomendada de aplicação

1. P-02 (config) e P-08 (conexão/DI): base para as demais mudanças.
2. P-03 (estrutura MVC) movendo o código existente sem alterar comportamento.
3. P-01, P-04, P-05, P-06 (segurança CRITICAL).
4. P-07, P-10, P-11, P-12 (fluxo, transações e erros).
5. P-09, P-13, P-14 (performance, deprecated, validação).
6. P-15, P-16 (legibilidade e limpeza).

Depois de cada bloco grande, rode a aplicação para detectar erros de import cedo.
