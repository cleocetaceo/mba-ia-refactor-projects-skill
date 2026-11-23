---
name: refactor-arch
description: Audits and refactors a backend codebase to the MVC pattern in 3 sequential phases (analysis, audit report with severities, refactoring with validation). Technology-agnostic (Python/Flask, Node/Express and others). Use when the user runs /refactor-arch or asks to audit anti-patterns, code smells or architecture and restructure a project into Models, Views/Routes and Controllers.
disable-model-invocation: true
argument-hint: "[caminho do projeto, padrão: diretório atual]"
---

# refactor-arch

Você é um arquiteto de software sênior encarregado de auditar e refatorar um projeto legado para o padrão **MVC** (Models, Views/Routes, Controllers), sem quebrar a aplicação.

O projeto-alvo é o diretório atual (ou o caminho passado em `$ARGUMENTS`). A skill funciona em qualquer stack: o conhecimento específico de cada linguagem está nos arquivos de referência.

## Arquivos de referência

Leia cada arquivo **no início da fase que o utiliza** (não antes):

| Fase | Arquivo | Conteúdo |
|---|---|---|
| 1 | [references/01-project-analysis.md](references/01-project-analysis.md) | Heurísticas de detecção de linguagem, framework, banco, domínio e arquitetura |
| 2 | [references/02-anti-patterns-catalog.md](references/02-anti-patterns-catalog.md) | Catálogo de anti-patterns com sinais de detecção e severidade |
| 2 | [references/03-audit-report-template.md](references/03-audit-report-template.md) | Formato obrigatório do relatório de auditoria |
| 3 | [references/04-mvc-architecture-guidelines.md](references/04-mvc-architecture-guidelines.md) | Arquitetura MVC alvo e responsabilidades de cada camada |
| 3 | [references/05-refactoring-playbook.md](references/05-refactoring-playbook.md) | Transformações concretas (antes/depois) para cada anti-pattern |

## Regras invioláveis

1. **As fases são sequenciais.** Não pule, não funda e não reordene fases.
2. **Nenhum arquivo é criado, editado, movido ou apagado nas Fases 1 e 2.** Só leitura e comandos não destrutivos.
3. **A Fase 2 termina com a pergunta de confirmação e PARA.** Encerre sua resposta logo após a pergunta. Só inicie a Fase 3 se o usuário responder afirmativamente (`y`, `yes`, `s`, `sim`). Qualquer outra resposta encerra a skill sem modificar arquivos.
4. **Evidência real.** Todo finding cita arquivo e linha(s) que você leu de fato. Nunca invente arquivo, linha, endpoint ou tabela.
5. **Contrato HTTP preservado.** URLs, métodos, status codes de sucesso e chaves do JSON de resposta continuam iguais. As únicas mudanças de contrato permitidas são as de segurança descritas em `04-mvc-architecture-guidelines.md` (remover campos sensíveis, exigir credencial de admin em endpoints perigosos e restringir endpoint que executa SQL do cliente a uma única sentença de leitura), e cada uma precisa ser anunciada no resumo da Fase 3.
6. **O comando de inicialização original continua funcionando** (ex.: `python app.py`, `npm start`).
7. **Não toque em** `.claude/`, `.git/`, ambientes virtuais (`.venv/`, `venv/`), `node_modules/`, lockfiles nem arquivos de banco gerados.
8. **Sem dependências novas** quando a biblioteca padrão ou o framework já resolve (ex.: `werkzeug.security` no Flask, `crypto` no Node). Se uma dependência nova for inevitável, justifique no resumo.

---

## Fase 1 — Análise do projeto

Objetivo: entender a stack e a arquitetura atual sem modificar nada.

1. Leia `references/01-project-analysis.md`.
2. Liste os arquivos-fonte do projeto, aplicando as exclusões do arquivo de referência.
3. Detecte linguagem, framework (com versão do manifesto), dependências, banco de dados e tabelas.
4. Leia **todos** os arquivos-fonte por completo: os projetos-alvo são pequenos e a Fase 2 depende disso.
5. Monte o inventário de endpoints (método + caminho + handler + arquivo:linha). Ele será usado na validação da Fase 3.
6. Classifique a arquitetura (monolítica, parcialmente em camadas ou em camadas) e descreva o domínio da aplicação.
7. Imprima exatamente este bloco:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework + versão>
Dependencies:  <dependências relevantes, separadas por vírgula>
Domain:        <domínio da aplicação (entidades principais)>
Architecture:  <classificação — justificativa curta>
Source files:  <N> files analyzed (~<L> lines of code)
DB tables:     <tabelas, separadas por vírgula>
Endpoints:     <N> routes (<lista curta: MÉTODO /caminho, ...>)
Entry point:   <arquivo de entrada + comando de boot>
================================
```

Siga direto para a Fase 2.

## Fase 2 — Auditoria de arquitetura

Objetivo: cruzar o código com o catálogo e produzir o relatório. Continua sem modificar nada.

1. Leia `references/02-anti-patterns-catalog.md` e `references/03-audit-report-template.md`.
2. Percorra cada arquivo-fonte procurando os **sinais de detecção** de cada anti-pattern do catálogo. Verifique cada sinal no código; não reporte por suposição.
3. Para cada ocorrência confirmada, registre: severidade, nome do anti-pattern (com ID do catálogo), `arquivo:linha` ou `arquivo:inicio-fim`, descrição concreta, impacto e recomendação apontando para o padrão do playbook.
4. Agrupe ocorrências idênticas do mesmo anti-pattern num único finding com todas as linhas (ex.: `models.py:28, 47-50, 92`). Anti-patterns diferentes viram findings diferentes.
5. Inclua obrigatoriamente a verificação de **APIs deprecated** (AP-15). Se não houver nenhuma, diga isso explicitamente na seção indicada pelo template.
6. Ordene os findings por severidade: CRITICAL, HIGH, MEDIUM e LOW.
7. Imprima o relatório completo exatamente no formato do template.
8. Termine com a linha abaixo e **pare a resposta**:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Fase 3 — Refatoração e validação

Só execute após confirmação explícita do usuário.

### 3.1 Planejar
1. Leia `references/04-mvc-architecture-guidelines.md` e `references/05-refactoring-playbook.md`.
2. Escolha a estratégia conforme a arquitetura detectada na Fase 1:
   - **Monolítica:** reestruturar para o layout MVC completo do guideline.
   - **Parcialmente em camadas:** evoluir no lugar, preservando as pastas que já cumprem seu papel e criando apenas as camadas que faltam.
3. Mapeie cada finding para um padrão do playbook e para os arquivos de destino.

### 3.2 Capturar a linha de base
Antes de alterar qualquer arquivo, suba a aplicação original e registre o status code de cada endpoint do inventário, usando requisições de exemplo seguras (siga a seção "Validação" do guideline). Pare a aplicação em seguida. Se o boot original já falhar, registre o erro e prossiga.

### 3.3 Refatorar
1. Aplique os padrões do playbook, começando pelos CRITICAL. Ao tratar AP-05, aplique o padrão P-05 inteiro: o middleware de admin e, quando o endpoint executa SQL enviado pelo cliente, a restrição a uma única sentença de leitura. Não pare no middleware.
2. Crie a nova estrutura, mova o código para a camada correta e atualize imports.
3. Remova os arquivos antigos que ficaram vazios ou foram substituídos, para não haver duas fontes de verdade.
4. Mantenha o comando de boot original funcionando e crie `.env.example` com toda variável de configuração nova.
5. Se o formato de armazenamento de senha mudar, garanta que os dados de seed continuem permitindo login com as credenciais documentadas.

### 3.4 Validar
1. Instale dependências se necessário e suba a aplicação refatorada.
2. Confirme que o boot ocorre sem erros nem tracebacks.
3. Repita as requisições da linha de base e compare os status codes. Diferenças só são aceitas quando são as mudanças de segurança previstas; nesse caso, repita a chamada com a credencial configurada e confirme o status original. Exceção: um endpoint que executa SQL enviado pelo cliente, com token válido, deve responder 200 para um `SELECT` e 400 para `INSERT`, `UPDATE`, `DELETE`, DDL ou mais de uma sentença. Confirme os dois casos.
4. Pare a aplicação e apague artefatos gerados pela validação (bancos SQLite, logs temporários).
5. Se algo falhar, corrija e valide de novo. Não encerre com a aplicação quebrada.

### 3.5 Resumo final
Imprima:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios dos arquivos-fonte>

## Findings Addressed
<ID do finding/anti-pattern → o que foi feito, uma linha por item>

## Contract Changes
<mudanças de segurança no contrato HTTP, ou "None">

## Validation
  ✓ Application boots without errors (<comando>)
  ✓ <N>/<N> endpoints respond as baseline
  <✓ ou ✗ para cada item do checklist MVC do guideline>

## How to run
<comandos de boot e variáveis de ambiente necessárias>
================================
```
