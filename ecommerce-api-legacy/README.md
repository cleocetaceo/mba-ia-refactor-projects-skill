# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`, agora organizada em camadas MVC.

## Como rodar

```bash
npm install
ADMIN_TOKEN=dev-admin-token npm start
```

No PowerShell: `$env:ADMIN_TOKEN = "dev-admin-token"; npm start`. Sem `ADMIN_TOKEN` a aplicação também sobe com `npm start`, mas os endpoints administrativos ficam desabilitados.

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Configuração

Todas as variáveis estão documentadas em `.env.example`. Copie para `.env` (carregado automaticamente no boot) ou exporte-as no shell.

| Variável | Default | Uso |
|---|---|---|
| `PORT` | `3000` | Porta HTTP |
| `HOST` | todas as interfaces | Interface de escuta |
| `DATABASE_PATH` | `:memory:` | Arquivo SQLite (em memória por padrão) |
| `PAYMENT_GATEWAY_KEY` | vazio | Chave do gateway (o gateway atual é simulado) |
| `ADMIN_TOKEN` | vazio | Token exigido no header `X-Admin-Token` pelos endpoints administrativos |

## Endpoints

| Método | Caminho | Autenticação |
|---|---|---|
| POST | `/api/checkout` | pública |
| GET | `/api/admin/financial-report` | `X-Admin-Token` |
| DELETE | `/api/users/:id` | `X-Admin-Token` |

Sem `ADMIN_TOKEN` configurado os endpoints administrativos respondem `403`; com token ausente ou inválido, `401`.

## Estrutura

```
src/
├── app.js            # composition root: config, banco, injeção de dependências, rotas, listen
├── config/           # variáveis de ambiente com defaults seguros
├── database/         # conexão (helpers com Promise + transações) e schema/seed
├── models/           # SQL parametrizado por entidade
├── controllers/      # casos de uso e validação de entrada
├── routes/           # camada View: express.Router por domínio
├── services/         # hash de senha (scrypt) e gateway de pagamento simulado
├── middlewares/      # autenticação de admin e handler central de erros
└── utils/            # logger, classes de erro, asyncHandler
```
