# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. O projeto segue o padrão MVC:

```
app.py              # entry point + composition root (create_app)
config/settings.py  # configuração via variáveis de ambiente (.env opcional)
database.py         # instância do Flask-SQLAlchemy
models/             # entidades, regras da entidade, consultas e serialização
controllers/        # casos de uso: validação, regras de negócio e transações
routes/             # camada View: Blueprints por domínio (tasks, users, categories, reports, health)
middlewares/        # tratamento central de erros e autenticação de admin
services/           # integrações (emissão de token assinado)
utils/helpers.py    # utilitários genéricos (datas UTC, percentuais)
```

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional: ajuste as variáveis
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (use `HOST=0.0.0.0` para expor na rede). O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo. **Rode-o antes do primeiro boot**, senão os endpoints retornam listas vazias.

Credenciais do seed: `joao@email.com` / `1234` (admin), `maria@email.com` / `abcd` (user), `pedro@email.com` / `pass` (manager).

## Variáveis de ambiente

Veja `.env.example`. As principais:

| Variável | Padrão | Uso |
|---|---|---|
| `SECRET_KEY` | aleatória por boot | Assinatura dos tokens de login |
| `DATABASE_URL` | `sqlite:///tasks.db` | URI do banco |
| `FLASK_DEBUG` | `false` | Debug do Flask (nunca em produção) |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Bind do servidor |
| `CORS_ORIGINS` | `*` | Origens liberadas no CORS |
| `ADMIN_TOKEN` | (vazio) | Credencial de admin (header `X-Admin-Token`) |

## Operações administrativas

Exigem o header `X-Admin-Token` com o valor de `ADMIN_TOKEN`. Sem token válido a resposta é `401`. Se `ADMIN_TOKEN` não estiver configurado, a resposta é `403`.

- `PUT /users/<id>`: altera nome, e-mail, senha, papel ou `active` (inclusive desativar outro usuário).
- `DELETE /users/<id>`: remove o usuário e as tasks dele.
- Campo `role` em `POST /users`: sem credencial de admin, o valor enviado é ignorado e o usuário é criado como `user`.

Senhas novas em `POST /users` e `PUT /users/<id>` precisam ter no mínimo 8 caracteres (`MIN_PASSWORD_LENGTH`). As senhas do seed continuam válidas no login.

```bash
ADMIN_TOKEN=troque-este-token python app.py
curl -X DELETE -H "X-Admin-Token: troque-este-token" http://127.0.0.1:5000/users/3
```
