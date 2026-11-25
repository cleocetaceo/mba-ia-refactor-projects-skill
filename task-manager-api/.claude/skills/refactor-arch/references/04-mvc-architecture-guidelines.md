# 04 — Guidelines da Arquitetura MVC Alvo (Fase 3)

Em uma API REST, o MVC se traduz assim:

```
Request → [View/Route] → [Controller] → [Model] → banco
                              │
                              └→ [Service] (efeitos externos: e-mail, pagamento, notificação)
Response ← [View/Route] ← (dados do Controller serializados)
```

## 1. Responsabilidades por camada

| Camada | Faz | Não faz |
|---|---|---|
| **Config** | Lê variáveis de ambiente, define defaults seguros para desenvolvimento, centraliza constantes de configuração | Lógica de negócio; secrets literais |
| **Model** | Acesso a dados (queries parametrizadas ou ORM), mapeamento linha → objeto/dict, invariantes da entidade (`is_overdue()`, `validate_status()`), serialização segura | Ler `request`, montar resposta HTTP, enviar e-mail |
| **View / Route** | Declara URL + método, extrai parâmetros do request, chama o controller, devolve a resposta com status code | SQL, regra de negócio, validação de domínio |
| **Controller** | Orquestra o caso de uso: valida entrada, aplica regras de negócio, chama models e services, controla transações, lança erros de domínio | Conhecer o framework HTTP (`request`, `res`) ou SQL |
| **Service** (opcional) | Integrações e efeitos colaterais: notificação, gateway de pagamento, hash de senha | Regra de negócio central |
| **Middleware** | Preocupações transversais: tratamento central de erros, autenticação de admin, log de requisição | Regra de um caso de uso específico |
| **Composition root** | Cria a app, carrega config, inicializa banco, injeta dependências, registra rotas e middlewares | Qualquer outra coisa |

Regra de dependência: **Route → Controller → Model/Service**. Nunca o contrário; models não importam controllers, controllers não importam o framework HTTP.

## 2. Layout alvo — projeto monolítico

### Python / Flask

```
<projeto>/
├── app.py                      # entry point fino: from src.app import create_app; app = create_app(); app.run(...)
├── requirements.txt
├── .env.example
└── src/
    ├── __init__.py
    ├── app.py                  # create_app(): config, db, error handlers, blueprints
    ├── config/
    │   ├── __init__.py
    │   └── settings.py         # os.environ.get(...) com defaults seguros
    ├── database.py             # conexão por request (flask.g) + init do schema/seed
    ├── models/
    │   ├── __init__.py
    │   └── <entidade>_model.py # uma por domínio
    ├── controllers/
    │   ├── __init__.py
    │   └── <dominio>_controller.py
    ├── views/
    │   ├── __init__.py         # register_blueprints(app)
    │   └── <dominio>_routes.py # Blueprint por domínio
    ├── services/               # só se houver efeitos externos
    └── middlewares/
        ├── __init__.py
        ├── error_handler.py    # @app.errorhandler + classes de erro
        └── auth.py             # decorator require_admin
```

### Node.js / Express

```
<projeto>/
├── package.json                # "start" continua funcionando
├── .env.example
└── src/
    ├── app.js                  # entry point/composition root: cria app, injeta deps, listen
    ├── config/index.js         # process.env com defaults seguros
    ├── database/
    │   ├── connection.js       # abre o banco e expõe helpers com Promise (run/get/all)
    │   └── schema.js           # criação de tabelas + seed
    ├── models/
    │   └── <entidade>.model.js # SQL parametrizado por entidade
    ├── controllers/
    │   └── <dominio>.controller.js
    ├── routes/                 # camada View: express.Router por domínio
    │   ├── index.js
    │   └── <dominio>.routes.js
    ├── services/               # pagamento, hash de senha, cache
    └── middlewares/
        ├── errorHandler.js     # (err, req, res, next)
        └── adminAuth.js
```

Use os nomes de pasta `views/` (Flask) ou `routes/` (Express) para a camada View. Ambos atendem ao checklist "Views/Routes separadas".

## 3. Projeto parcialmente em camadas — evoluir no lugar

Quando a Fase 1 classificar o projeto como **parcialmente em camadas** (já existem `models/`, `routes/`, `services/`, `utils/`):

1. **Não mova o que já está no lugar certo.** `models/` continua sendo Model; `routes/` continua sendo a camada View.
2. **Crie apenas o que falta:** `controllers/` (regras que hoje estão nas rotas), `config/` (settings via env), `middlewares/` (erro central e auth).
3. **Emagreça as rotas:** cada handler passa a ter poucas linhas (extrair parâmetros → chamar controller → responder).
4. **Corrija fronteiras de domínio:** rotas de um domínio no arquivo de outro vão para um arquivo próprio (ex.: `routes/category_routes.py`), mantendo as mesmas URLs.
5. **Reaproveite o que já existe:** métodos do model (`is_overdue()`, `to_dict()`) e helpers úteis substituem cópias inline; helpers mortos são removidos.
6. **Introduza `create_app()`** e mantenha `app.py` exportando `app` se outros scripts o importam (ex.: `seed.py` faz `from app import app, db`).

## 4. Regras transversais obrigatórias

### Configuração
- Todo secret vem de variável de ambiente. Para `SECRET_KEY` em desenvolvimento, gere um valor aleatório no boot (`secrets.token_hex(32)` / `crypto.randomBytes(32)`) quando a variável não existir, em vez de usar um literal.
- `DEBUG` vem de env com default `False`. Host e porta vêm de env, mantendo como default a porta original do projeto.
- Documente todas as variáveis em `.env.example`, sem valores reais.

### Banco de dados
- Queries sempre parametrizadas.
- Conexão por request ou injetada, nunca uma global mutável compartilhada entre threads.
- Escritas multi-etapa dentro de transação.
- Schema e seed continuam sendo criados no mesmo momento de antes (ex.: no boot), para a app subir com os mesmos dados de exemplo.

### Segurança e mudanças de contrato permitidas
Estas são as **únicas** alterações de contrato HTTP aceitas, e cada uma deve aparecer em "Contract Changes" no resumo da Fase 3:

1. **Remover campos sensíveis das respostas** (senha, hash, secret, caminho do banco). As demais chaves permanecem.
2. **Exigir credencial de admin em endpoints perigosos**, em tudo o que o Impact do finding descreve: execução de SQL, reset de banco, exclusões administrativas, relatórios financeiros, e mutação de conta alheia (rebaixar papel, desativar via `active`, trocar e-mail ou senha, apagar o usuário e os dados dele). Padrão: header `X-Admin-Token` comparado (com `hmac.compare_digest` / `crypto.timingSafeEqual`) ao valor da variável `ADMIN_TOKEN`. Sem token válido → `401`. Se `ADMIN_TOKEN` não estiver definido, o endpoint fica desabilitado (`403`). Com token válido, o endpoint responde exatamente como antes. **Exceção:** o endpoint que executa SQL enviado pelo cliente fica restrito à leitura mesmo com token válido. Aceite apenas uma única sentença de leitura (`SELECT`, ou `WITH` ... `SELECT`), sem `;` adicional. `INSERT`, `UPDATE`, `DELETE`, DDL e múltiplas sentenças respondem `400`. Um `SELECT` com token válido devolve o mesmo JSON de sucesso de antes. Registre essa divergência em Contract Changes.
3. **Não aceitar privilégio nem mutação de conta enviados pelo cliente.** Na criação, `role`/`tipo` privilegiado sem credencial de admin usa o default. Na atualização, a rota que altera `role`/`tipo`, `active`, e-mail ou senha de um usuário existente exige a credencial do item 2. Ignorar só `role` e gravar `active`, e-mail e senha não satisfaz a regra.
4. **Senhas com hash forte** (`werkzeug.security.generate_password_hash` / `crypto.scrypt`). O login com as credenciais do seed precisa continuar funcionando. Se a auditoria apontar senha mínima de 4 caracteres, o default de `MIN_PASSWORD_LENGTH` passa a ser no mínimo 8 no código e no `.env.example`.

Atualize arquivos de requisição de exemplo (`api.http`, README) quando um endpoint passar a exigir header.

### Erros
- Um handler central converte exceções de domínio (`NotFoundError`, `ValidationError`) em JSON com o status adequado e o mesmo formato de corpo que a API já usava (ex.: `{"erro": "..."}` ou `{"error": "..."}`).
- Erros inesperados viram `500` com mensagem genérica; o detalhe vai para o log, não para o cliente.

### Logging
- Substitua `print`/`console.log` de eventos por `logging`/um logger simples com nível. Nunca registre senha, cartão ou token.

## 5. Validação (Fases 3.2 e 3.4)

Procedimento para comprovar que a aplicação continua funcionando:

1. **Ambiente:** use o venv do projeto, se existir; instale dependências se faltarem (`pip install -r requirements.txt`, `npm install`).
2. **Dados:** se o README exige seed (`python seed.py`), rode-o antes do boot. Apague bancos SQLite gerados pela linha de base antes de validar a versão refatorada, para o seed ser recriado no formato novo.
3. **Boot em background**, guardando o PID e o log:
   ```bash
   (python app.py > /tmp/app.log 2>&1 &) ; sleep 3     # ou: npm start > /tmp/app.log 2>&1 &
   ```
   Defina as variáveis necessárias na mesma linha (ex.: `ADMIN_TOKEN=dev-token python app.py`).
4. **Requisições:** para cada endpoint do inventário, envie uma requisição segura e registre o status:
   ```bash
   curl -s -o /dev/null -w "%{http_code} GET /produtos\n" http://localhost:5000/produtos
   curl -s -o /dev/null -w "%{http_code} POST /login\n" -H "Content-Type: application/json" \
        -d '{"email":"joao@email.com","senha":"123456"}' http://localhost:5000/login
   ```
   - Use payloads dos arquivos de exemplo (`api.http`) e dados do seed.
   - Teste ao menos um caso de erro por recurso (ID inexistente → 404, payload inválido → 400).
   - Endpoints destrutivos (reset de banco, delete) vão por último.
5. **Encerrar:** finalize o processo pelo PID ou pela porta (`kill`, `taskkill //PID <pid> //F` no Git Bash do Windows) e confirme que a porta foi liberada.
6. **Comparar:** monte a tabela `endpoint | status baseline | status refatorado | ok?`. Toda divergência precisa ser uma mudança de contrato permitida (seção 4).

## 6. Checklist MVC (para o resumo da Fase 3)

- [ ] Estrutura de diretórios segue o padrão MVC (models, views/routes, controllers)
- [ ] Configuração extraída para módulo de config (sem secrets hardcoded)
- [ ] Models abstraem o acesso a dados com queries seguras
- [ ] Views/Routes apenas roteiam e serializam
- [ ] Controllers concentram o fluxo e as regras da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro (composition root)
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem como na linha de base
