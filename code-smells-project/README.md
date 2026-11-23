# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`, já refatorada para MVC.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas gravadas com hash). Bancos antigos com senhas em texto puro são migrados para hash no boot.

### Configuração

Toda a configuração vem de variáveis de ambiente, documentadas em [`.env.example`](.env.example). As principais:

| Variável | Default | Uso |
|---|---|---|
| `ADMIN_TOKEN` | (vazio) | Token dos endpoints administrativos. Sem ele, esses endpoints respondem 403 |
| `SECRET_KEY` | aleatória por boot | Chave de assinatura do Flask |
| `FLASK_DEBUG` | `false` | Debug do Flask |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Endereço do servidor (`HOST=0.0.0.0` expõe na rede) |
| `DATABASE_PATH` | `loja.db` | Arquivo SQLite |

Exemplo (Git Bash / Linux / macOS):

```bash
ADMIN_TOKEN=troque-este-token python app.py
```

PowerShell:

```powershell
$env:ADMIN_TOKEN = "troque-este-token"; python app.py
```

### Endpoints administrativos

`POST /admin/reset-db`, `POST /admin/query` e `GET /relatorios/vendas` exigem o header `X-Admin-Token` com o valor de `ADMIN_TOKEN`:

```bash
curl -H "X-Admin-Token: troque-este-token" http://localhost:5000/relatorios/vendas
curl -X POST -H "X-Admin-Token: troque-este-token" -H "Content-Type: application/json" \
     -d '{"sql": "SELECT id, nome FROM produtos"}' http://localhost:5000/admin/query
```

`/admin/query` aceita apenas uma única sentença de leitura (`SELECT` ou `WITH ... SELECT`); qualquer outra sentença responde `400`.

### Usuários de exemplo

| E-mail | Senha | Tipo |
|---|---|---|
| admin@loja.com | admin123 | admin |
| joao@email.com | 123456 | cliente |
| maria@email.com | senha123 | cliente |

## Estrutura

```
app.py                 # entry point fino (python app.py)
src/
├── app.py             # create_app(): config, banco, erros, blueprints
├── config/            # settings via variáveis de ambiente
├── database/          # conexão por request, schema e seed
├── models/            # acesso a dados por domínio (SQL parametrizado)
├── controllers/       # casos de uso e validação
├── views/             # Blueprints (rotas HTTP)
├── services/          # hash de senha, notificações
└── middlewares/       # handler central de erros, autenticação de admin
```
