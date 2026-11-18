# Audit Report — Projeto 2: ecommerce-api-legacy

Saída da skill `/refactor-arch` (Claude Code 2.1.327, modelo Opus) executada em `ecommerce-api-legacy/`.
A seção Fase 2 é o relatório de auditoria; a Fase 1 aparece antes como contexto.

## Fase 1 — Análise

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js — runtime local v25.2.1)
Framework:     Express ^4.18.2 (4.22.1 instalado)
Dependencies:  express ^4.18.2, sqlite3 ^5.1.6 (driver cru, 5.1.7 instalado) — sem ORM, validação, auth ou logger
Domain:        LMS com checkout de cursos (usuários, cursos, matrículas, pagamentos, logs de auditoria)
Architecture:  Monolítica — 3 arquivos em src/ sem pastas por camada; a classe AppManager (141 linhas) concentra conexão, schema/seed, rotas HTTP, regra de pagamento e relatório
Source files:  3 files analyzed (~180 lines of code)
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite ':memory:', seed no boot)
Endpoints:     3 routes (POST /api/checkout, GET /api/admin/financial-report, DELETE /api/users/:id)
Entry point:   src/app.js — npm start (node src/app.js), porta 3000 fixa em src/utils.js:6
================================
```

## Fase 2 — Relatório de auditoria

```text
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.18.2 (^4.18.2 no manifesto; 4.22.1 instalado)
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 5 | HIGH: 6 | MEDIUM: 3 | LOW: 4

## Findings

### [CRITICAL] Credenciais e secrets hardcoded (AP-02)
File: src/utils.js:1-7
Description: O objeto literal `const config = { dbUser: "admin_master", dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_1234567890abcdef", smtpUser: "no-reply@fullcycle.com.br", port: 3000 }` está versionado. A chave de produção `pk_live_` é lida no checkout (src/AppManager.js:45).
Impact: Quem tem acesso ao repositório obtém a chave do gateway de pagamento e a senha do banco. Trocar qualquer credencial exige um novo deploy.
Recommendation: Criar src/config/index.js que lê process.env (PORT, PAYMENT_GATEWAY_KEY, DB_PATH, ADMIN_TOKEN), com defaults não sensíveis apenas para dev, documentar em .env.example e remover os literais (Playbook P-02).

### [CRITICAL] God Class / God Module (AP-03)
File: src/AppManager.js:4-139
Description: A classe `AppManager` cria a conexão (`new sqlite3.Database(':memory:')`, linha 7), define o schema e o seed (`initDb`, 10-23) e registra as rotas HTTP de 3 domínios num único método `setupRoutes` de 113 linhas (25-138): checkout/pagamento (28-78), relatório financeiro (80-129) e usuários (131-137).
Impact: Nenhuma regra pode ser testada sem subir Express e SQLite. Qualquer mudança no checkout pode quebrar o relatório ou a exclusão de usuários.
Recommendation: Separar em src/config/database.js (conexão, schema e seed), src/models/* (um por tabela, com placeholders ?), src/services/* (checkout, relatório, usuário), src/controllers/*, src/routes/* e src/app.js só para composição (Playbook P-03).

### [CRITICAL] Armazenamento inseguro de senha / criptografia fraca (AP-04)
File: src/utils.js:17-23, src/AppManager.js:18, 68
Description: `badCrypto(pwd)` concatena os 2 primeiros caracteres do base64 da senha 10000 vezes e corta em 10. O "hash" só depende do 1º byte e de metade do 2º, então "senhaforte", "senha123" e "se" geram o mesmo "c2c2c2c2c2". Não há salt e o resultado é reversível. Quando `pwd` não é enviado, a senha padrão é `p || "123456"` (68), e o seed grava a senha '123' em texto puro (18).
Impact: Com acesso ao banco, as senhas são recuperáveis na hora. Colisões em massa permitem login com senhas diferentes da cadastrada, e contas criadas sem pwd ganham uma senha conhecida.
Recommendation: Usar crypto.scrypt (nativo do Node) com salt aleatório por usuário, comparar com crypto.timingSafeEqual, remover o default "123456" e gravar o seed já com hash (Playbook P-04).

### [CRITICAL] Endpoint perigoso sem autenticação (AP-05)
File: src/AppManager.js:80, 131
Description: GET /api/admin/financial-report devolve a receita por curso e o nome dos alunos pagantes, e DELETE /api/users/:id apaga qualquer usuário pelo id. Nenhuma das duas rotas verifica credencial.
Impact: Qualquer cliente anônimo lê dados financeiros e pessoais e consegue apagar todos os usuários iterando ids.
Recommendation: Criar o middleware src/middlewares/requireAdmin.js, que valida um token de admin vindo de variável de ambiente comparado com timingSafeEqual, e aplicá-lo às duas rotas (Playbook P-05).

### [CRITICAL] Exposição de dados sensíveis (AP-06)
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` grava o número completo do cartão e a chave pk_live a cada checkout. Confirmei executando: o log mostrou "Processando cartão 4111222233334444 na chave pk_live_1234567890abcdef".
Impact: Violação de PCI-DSS e LGPD. Os logs passam a conter números de cartão e a credencial do gateway.
Recommendation: Remover o log. Se for preciso registrar o evento, usar o logger central com o cartão mascarado (só os últimos 4 dígitos) e nunca a chave (Playbook P-06).

### [HIGH] Regra de negócio na rota/controller (Fat Controller) (AP-07)
File: src/AppManager.js:28-78, 80-129
Description: O handler de POST /api/checkout (51 linhas) faz tudo dentro da rota: valida, busca o curso, busca ou cria o usuário, gera o hash da senha, decide a aprovação do pagamento (`cc.startsWith("4") ? "PAID" : "DENIED"`), cria matrícula, pagamento e auditoria e grava o cache. O GET /api/admin/financial-report (50 linhas) calcula a receita (`courseData.revenue += payment.amount` só quando 'PAID') e monta o DTO na própria rota. Os dois são fluxos de dinheiro.
Impact: As regras de cobrança e de receita só podem ser testadas via HTTP e não podem ser reutilizadas.
Recommendation: Mover as regras para src/services/checkoutService.js e src/services/reportService.js. Os controllers só leem o req, chamam o service e mapeiam o resultado para status e corpo (Playbook P-07).

### [HIGH] Estado global mutável (AP-08)
File: src/utils.js:9-10, 12-15, 25, src/AppManager.js:59
Description: `let globalCache = {}` e `let totalRevenue = 0` ficam no escopo do módulo e são exportados. `logAndCache` muta `globalCache[\`last_checkout_${userId}\`]` a cada checkout (AppManager.js:59), sem limite e sem nenhuma leitura.
Impact: O estado vaza entre requisições e entre testes, a memória cresce sem limite e o comportamento diverge com mais de uma instância.
Recommendation: Remover o cache global, que só recebe escritas. Se um cache for necessário, ele deve ser um serviço injetado com escopo e limite definidos (Playbook P-08).

### [HIGH] Acoplamento forte sem injeção de dependência (AP-09)
File: src/AppManager.js:1, 7
Description: A mesma classe que define as rotas importa o driver (`require('sqlite3').verbose()`) e instancia a conexão concreta no construtor (`this.db = new sqlite3.Database(':memory:')`), com o caminho do banco fixo.
Impact: Não dá para usar um banco de teste nem trocar a infraestrutura sem editar a classe que contém as regras e as rotas.
Recommendation: src/config/database.js cria a conexão (DB_PATH via env, default ':memory:') e a injeta nos models. Os services recebem os models e os controllers recebem os services (Playbook P-08).

### [HIGH] Escrita multi-etapa sem transação (AP-10)
File: src/AppManager.js:50-61, 69-71, 133-135
Description: O checkout faz até 4 escritas independentes (INSERT users 69, enrollments 50, payments 54, audit_logs 57) sem BEGIN/COMMIT/ROLLBACK. Se o INSERT de payments falhar, a matrícula fica sem pagamento. O usuário é criado antes da decisão do cartão, então persiste mesmo com "Pagamento recusado"; confirmei isso numa execução real em que o usuário foi gravado e o processo caiu antes da matrícula. O DELETE /api/users/:id apaga só `users` e deixa enrollments e payments órfãos, e a própria resposta admite: "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."
Impact: Dados financeiros inconsistentes (matrícula sem pagamento), usuários fantasmas e registros órfãos.
Recommendation: Validar o pagamento antes de qualquer escrita e executar usuário + matrícula + pagamento + auditoria numa única transação no service. No DELETE, remover payments → enrollments → user na mesma transação (Playbook P-10).

### [HIGH] Callback hell / fluxo assíncrono aninhado (AP-12)
File: src/AppManager.js:26, 37-77, 83-128, 57, 92-93, 104, 106, 133-135
Description: O checkout encadeia 5 níveis de callbacks (db.get → db.get → db.run → db.run → db.run) e alterna `this.db` com `self.db` por causa de `function(err)` (26, 54). O relatório controla o fim das queries com contadores manuais `coursesPending` e `enrPending` (86, 93, 117-122), por isso a ordem dos cursos no JSON não é determinística: a execução real devolveu "Docker" antes de "Clean Architecture". Vários erros são ignorados: o callback de audit_logs (57), `enrollments.length` acessado sem checar `err` (93), as linhas 104 e 106, e o DELETE, que responde sucesso mesmo com erro (133-135).
Impact: Fluxo ilegível, erros engolidos, risco de resposta nunca enviada ou TypeError que derruba o processo, e saída instável entre execuções.
Recommendation: Envolver o driver em helpers que retornam Promise (run/get/all) e reescrever com async/await e try/catch → next(err) (Playbook P-11).

### [HIGH] Validação de entrada ausente ou fraca (AP-16)
File: src/AppManager.js:29-35, 46, 132
Description: O checkout só verifica se `usr`, `eml`, `c_id` e `card` estão preenchidos (35). Não há checagem de tipo nem de formato. Com `"card": 4111222233334444` (número), `cc.startsWith` lança TypeError dentro do callback do sqlite3, e essa exceção não capturada derruba o servidor inteiro (reproduzido). O e-mail não é validado, `c_id` não é checado como inteiro e `req.params.id` do DELETE (132) não é validado. A severidade subiu de MEDIUM para HIGH por ser fluxo de pagamento.
Impact: Uma única requisição malformada tira a API do ar, e dados inválidos são persistidos.
Recommendation: Validar o payload no controller (strings não vazias, e-mail com formato válido, card como string de dígitos, c_id inteiro positivo) e responder 400 "Bad Request" como hoje (Playbook P-14).

### [MEDIUM] Queries N+1 (AP-13)
File: src/AppManager.js:83, 92, 104, 106
Description: O relatório faz 1 SELECT de courses, depois 1 SELECT de enrollments por curso (92) e mais 2 SELECTs (users em 104, payments em 106) por matrícula, ou seja, 1 + C + 2E queries.
Impact: A latência do relatório cresce linearmente com o número de matrículas.
Recommendation: Usar um único SELECT com LEFT JOIN courses → enrollments → users → payments e agregar no service (Playbook P-09).

### [MEDIUM] Tratamento de erro genérico / sem handler central (AP-17)
File: src/app.js:5-14, src/AppManager.js:35, 38, 41, 48, 51, 55, 70, 84
Description: Não existe middleware `app.use((err, req, res, next) => ...)`. Cada rota responde texto puro com mensagens ad hoc ("Bad Request", "Erro DB", "Erro Matrícula", "Erro Pagamento", "Erro ao criar usuário"), enquanto os sucessos são JSON. Em `if (err || !course)` (38), uma falha do banco é mascarada como 404 "Curso não encontrado".
Impact: Erros reais ficam invisíveis ou mal classificados, e exceções fora do fluxo do Express derrubam o processo.
Recommendation: Criar classes de erro (AppError/NotFoundError/ValidationError) e um errorHandler central em src/middlewares/errorHandler.js que preserve os status e os corpos atuais (Playbook P-12).

### [MEDIUM] Responsabilidade no módulo errado (AP-18)
File: src/utils.js:1-25
Description: O módulo genérico `utils.js` mistura configuração da aplicação (`config`, 1-7), cache em memória (`logAndCache`, 9-15) e hash de senha, que é regra de domínio (`badCrypto`, 17-23).
Impact: Configuração, infraestrutura e segurança ficam num lugar sem coesão, e fica difícil achar e testar cada uma.
Recommendation: Mover a configuração para src/config/index.js e o hash de senha para src/utils/password.js (ou src/services/), e eliminar o cache (Playbook P-03).

### [LOW] Magic numbers e strings (AP-19)
File: src/AppManager.js:21, 46, 48, 108, src/utils.js:6
Description: A regra de aprovação `cc.startsWith("4")` não tem nome. Os status `"PAID"` e `"DENIED"` aparecem como strings soltas em 4 pontos, e a porta `3000` é literal.
Impact: A regra de aprovação fica implícita e uma mudança de status precisa ser feita em vários lugares.
Recommendation: Criar constantes `PAYMENT_STATUS = { PAID, DENIED }` e `APPROVED_CARD_PREFIX` no domínio de pagamento, e usar PORT da config (Playbook P-15).

### [LOW] Nomenclatura ruim (AP-20)
File: src/AppManager.js:4, 26, 29-33, src/utils.js:12, 17, src/app.js:13
Description: Há variáveis crípticas (`u`, `e`, `p`, `cid`, `cc`), `const self = this` para contornar `function(){}`, nomes genéricos ou enganosos (`AppManager`, `logAndCache`, `badCrypto`) e o log "Frankenstein LMS" num projeto chamado ecommerce-api.
Impact: O código é mais difícil de ler e revisar.
Recommendation: Renomear as variáveis internas (userName, email, password, courseId, cardNumber) mantendo os campos públicos `usr`, `eml`, `pwd`, `c_id` e `card` do contrato (Playbook P-15).

### [LOW] console.log como logging (AP-21)
File: src/AppManager.js:45, src/utils.js:13, src/app.js:13
Description: Eventos de negócio ("[LOG] Salvando no cache") e de boot são registrados com `console.log`, sem nível nem formato.
Impact: Não dá para filtrar por severidade nem silenciar logs de debug em produção.
Recommendation: Criar um logger mínimo em src/utils/logger.js (info/warn/error sobre console) e usá-lo nos pontos necessários (Playbook P-16).

### [LOW] Código, import ou dependência morta (AP-22)
File: src/AppManager.js:2, 104, src/utils.js:2-3, 5, 10, 25
Description: `totalRevenue` é importado (AppManager.js:2) e nunca usado, e é declarado (utils.js:10) sem nunca ser alterado. `globalCache` é exportado (25) mas nunca importado. `dbUser`, `dbPass` e `smtpUser` (utils.js:2, 3, 5) nunca são lidos. A coluna `email` é selecionada em 104 e descartada.
Impact: Ruído que esconde o que de fato é usado e mantém secrets versionados sem necessidade.
Recommendation: Remover os símbolos, as chaves de config e as colunas não usadas (Playbook P-16).

## Deprecated APIs
None detected — verified against catalog AP-15 (src/utils.js:20 já usa Buffer.from; src/app.js:6 usa express.json() em vez de body-parser; as respostas usam res.status(s).send/json; sqlite3 não está marcado como deprecated no registry npm)

## Endpoint Inventory
POST /api/checkout — src/AppManager.js:28
GET /api/admin/financial-report — src/AppManager.js:80
DELETE /api/users/:id — src/AppManager.js:131

================================
Total: 18 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
