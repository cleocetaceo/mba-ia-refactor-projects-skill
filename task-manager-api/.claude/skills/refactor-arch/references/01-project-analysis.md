# 01 — Análise de Projeto (Fase 1)

Heurísticas para detectar stack, banco de dados, domínio e arquitetura de qualquer projeto backend. Use evidências de arquivos reais; quando uma heurística não se aplicar, diga "não detectado" em vez de supor.

## 1. Inventário de arquivos

**Arquivos-fonte** são os arquivos de código da aplicação escritos pelo time.

Exclua sempre:

| Categoria | Padrões |
|---|---|
| Ferramentas/IA | `.claude/`, `.cursor/`, `.github/`, `.vscode/`, `.idea/` |
| Controle de versão | `.git/` |
| Dependências instaladas | `node_modules/`, `.venv/`, `venv/`, `env/`, `vendor/`, `site-packages/` |
| Artefatos gerados | `__pycache__/`, `*.pyc`, `dist/`, `build/`, `coverage/`, `*.db`, `*.sqlite`, `*.log` |
| Lockfiles | `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, `Pipfile.lock` |

Conte separadamente (não entram em "Source files", mas são lidos): manifestos (`requirements.txt`, `package.json`, `pyproject.toml`, `go.mod`, `pom.xml`), `README.md`, arquivos de requisições de exemplo (`*.http`, coleções Postman) e scripts de seed.

Para estimar linhas de código, some as linhas dos arquivos-fonte (ex.: `wc -l` nos arquivos listados).

## 2. Linguagem

| Evidência | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, arquivos `*.py` | Python |
| `package.json` + `*.js`/`*.mjs`/`*.cjs` | JavaScript (Node.js) |
| `package.json` + `tsconfig.json` + `*.ts` | TypeScript (Node.js) |
| `go.mod` | Go |
| `pom.xml`, `build.gradle` | Java/Kotlin |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| `*.csproj` | C# |

Se houver mais de uma, a linguagem principal é a do entry point.

## 3. Framework e versão

Leia a versão no manifesto (`flask==3.1.1`, `"express": "^4.18.2"`). Confirme pelo código:

| Framework | Sinais no código |
|---|---|
| Flask | `from flask import Flask`, `Flask(__name__)`, `@app.route`, `Blueprint(`, `app.add_url_rule(` |
| FastAPI | `from fastapi import FastAPI`, `@app.get(`, `APIRouter(` |
| Django | `manage.py`, `settings.py`, `urls.py`, `django.` nos imports |
| Express | `require('express')` ou `import express`, `express()`, `app.get(`/`app.post(`, `express.Router()` |
| NestJS | `@nestjs/core`, decorators `@Controller()` |
| Koa / Fastify / Hapi | `require('koa')`, `fastify(`, `@hapi/hapi` |
| Spring | `@SpringBootApplication`, `@RestController` |
| Gin / Echo | `gin.Default()`, `echo.New()` |

Liste em "Dependencies" as bibliotecas relevantes do manifesto (ORM, driver de banco, CORS, validação, auth). Indique dependências declaradas mas não importadas em nenhum arquivo: isso é sinal de AP-22 (código ou dependência morta).

## 4. Banco de dados e tabelas

| Evidência | Banco / acesso |
|---|---|
| `import sqlite3`, `sqlite3.connect(` | SQLite via driver cru (SQL manual) |
| `flask_sqlalchemy`, `SQLAlchemy()`, `db.Model` | SQLAlchemy ORM (URI em `SQLALCHEMY_DATABASE_URI`) |
| `require('sqlite3')`, `new sqlite3.Database(` | SQLite via driver cru (Node). `':memory:'` significa banco volátil |
| `pg`, `psycopg2`, `mysql2`, `pymysql` | PostgreSQL / MySQL |
| `mongoose`, `pymongo` | MongoDB |
| `prisma`, `sequelize`, `typeorm`, `knex` | ORMs/query builders Node |

**Tabelas:** extraia de `CREATE TABLE <nome>`, de `__tablename__ = '<nome>'`, de modelos ORM ou de migrations. Liste todas.

## 5. Entry point e comando de boot

| Stack | Onde procurar |
|---|---|
| Python | arquivo com `if __name__ == '__main__':` + `app.run(`; README ("Como rodar") |
| Node | `scripts.start` e `main` do `package.json`; arquivo com `app.listen(` |

Registre a porta (`port=5000`, `config.port`, `PORT`) e os passos prévios documentados (ex.: `python seed.py`). O comando de boot original precisa continuar funcionando depois da Fase 3.

**Ambiente de execução:** se existir `.venv/` ou `venv/`, use o interpretador dele (`.venv/Scripts/python` no Windows, `.venv/bin/python` no Linux/macOS). Se `node_modules/` não existir, a validação precisará de `npm install`.

## 6. Inventário de endpoints

Encontre todas as rotas:

| Stack | Padrões de busca |
|---|---|
| Flask | `@app.route(`, `@<bp>.route(`, `app.add_url_rule(`, `methods=[...]` (sem `methods`, o padrão é GET) |
| Express | `app.get/post/put/patch/delete(`, `router.<verbo>(`, `app.use('<prefixo>', router)` |
| FastAPI | `@app.<verbo>(`, `@router.<verbo>(` |

Para cada rota registre: método, caminho completo (com prefixo de blueprint/router), handler e `arquivo:linha`. Inclua rotas inline (`@app.route('/')`) e rotas administrativas.

Arquivos de exemplo (`api.http`, README) mostram payloads válidos: use-os na validação da Fase 3.

## 7. Domínio da aplicação

Infira o domínio cruzando:

1. nomes das tabelas e modelos (`produtos`, `pedidos` → e-commerce; `courses`, `enrollments` → LMS; `tasks`, `categories` → gerenciador de tarefas);
2. prefixos de rotas (`/checkout`, `/reports`, `/admin`);
3. README e nome do projeto.

Formato: `<tipo de sistema> (<entidades principais>)`, ex.: `E-commerce API (produtos, pedidos, usuários)`.

## 8. Classificação da arquitetura

| Classificação | Sinais | Estratégia na Fase 3 |
|---|---|---|
| **Monolítica / God Class** | Poucos arquivos (1–5) na raiz; um arquivo ou classe concentra rotas + SQL + regras; não há pastas por camada | Reestruturar para o layout MVC completo |
| **Parcialmente em camadas** | Existem pastas como `models/`, `routes/`, `services/`, `utils/`, mas há regra de negócio nas rotas, serviços sem uso, config hardcoded e domínios misturados | Evoluir no lugar: preservar o que funciona e criar as camadas que faltam (controllers, config, middlewares) |
| **Em camadas (MVC/Clean)** | Rotas finas, controllers/services com regra, models isolados, config externa, error handler central | Apenas correções pontuais dos findings |

Descreva a classificação com uma justificativa curta e concreta, ex.: `Monolítica — 4 arquivos na raiz; models.py concentra SQL de 4 domínios`.

## 9. Checklist de saída da Fase 1

- [ ] Linguagem e framework (com versão) confirmados no manifesto e no código
- [ ] Contagem de arquivos-fonte sem pastas excluídas
- [ ] Todas as tabelas listadas
- [ ] Todos os endpoints inventariados, com `arquivo:linha`
- [ ] Entry point, porta e comando de boot identificados
- [ ] Domínio e arquitetura descritos com evidência
