# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`, reestruturada no padrão MVC.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas gravadas com hash):

| E-mail | Senha | Tipo |
|---|---|---|
| admin@loja.com | admin123 | admin |
| joao@email.com | 123456 | cliente |
| maria@email.com | senha123 | cliente |

## Configuração

Todas as configurações vêm de variáveis de ambiente (veja `.env.example`). As principais:

| Variável | Default | Uso |
|---|---|---|
| `ADMIN_TOKEN` | (vazio → endpoints admin desabilitados, 403) | Token exigido no header `X-Admin-Token` |
| `SECRET_KEY` | aleatória a cada boot | Assinatura de sessões |
| `FLASK_DEBUG` | `false` | Modo debug |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Bind do servidor |
| `DATABASE_PATH` | `loja.db` | Arquivo SQLite |

Exemplo (Git Bash / Linux / macOS):

```bash
ADMIN_TOKEN=troque-este-token python app.py
```

PowerShell:

```powershell
$env:ADMIN_TOKEN = "troque-este-token"; python app.py
```

## Endpoints administrativos

`POST /admin/reset-db`, `POST /admin/query` e `GET /relatorios/vendas` exigem o header `X-Admin-Token`:

```bash
curl -H "X-Admin-Token: troque-este-token" http://localhost:5000/relatorios/vendas
```

Sem token válido → `401`; com `ADMIN_TOKEN` não configurado → `403`.

## Estrutura

```
app.py                 # entry point (python app.py)
src/
├── app.py             # create_app(): config, banco, middlewares, blueprints
├── config/            # settings via variáveis de ambiente
├── database/          # conexão por request, schema e seed
├── models/            # acesso a dados (SQL parametrizado) por entidade
├── controllers/       # casos de uso, validação e regras de negócio
├── views/             # blueprints Flask (rotas)
├── services/          # hash de senha, notificações
└── middlewares/       # tratamento central de erros, autenticação admin
```
