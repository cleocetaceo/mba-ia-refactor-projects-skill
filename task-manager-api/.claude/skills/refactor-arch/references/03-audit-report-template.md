# 03 — Template do Relatório de Auditoria (Fase 2)

O relatório da Fase 2 deve seguir **exatamente** este formato. Os rótulos ficam em inglês; descrições, impactos e recomendações ficam em português.

## Template

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta do projeto>
Stack:   <Linguagem> + <Framework> <versão>
Files:   <N> analyzed | ~<L> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Nome do anti-pattern> (AP-XX)
File: <arquivo>:<linha ou inicio-fim>[, <arquivo>:<linhas>...]
Description: <o que acontece, citando o trecho/identificador real>
Impact: <consequência concreta para segurança, manutenção ou dados>
Recommendation: <transformação a aplicar> (Playbook P-XX)

### [HIGH] ...

### [MEDIUM] ...

### [LOW] ...

## Deprecated APIs
<uma linha por API: arquivo:linha — API atual → substituto moderno>
<ou: "None detected — verified against catalog AP-15">

## Endpoint Inventory
<MÉTODO /caminho — arquivo:linha, um por linha>

================================
Total: <n> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Regras de preenchimento

1. **Ordem:** todos os CRITICAL, depois HIGH, MEDIUM e LOW. Dentro da mesma severidade, ordene pelo ID do catálogo.
2. **Summary consistente:** a soma das severidades é igual ao `Total`, e cada contagem bate com o número de blocos `###` daquela severidade.
3. **`File:` exato:** caminho relativo à raiz do projeto + linha (`app.py:7`) ou intervalo (`models.py:1-314`). Para várias ocorrências do mesmo anti-pattern, liste todas na mesma linha separadas por vírgula. Confira os números de linha no arquivo antes de escrever.
4. **Description concreta:** cite o identificador, a string ou o trecho real (`SECRET_KEY = "minha-chave-super-secreta-123"`, função `badCrypto`). Proibido texto genérico como "código ruim".
5. **Um finding por anti-pattern:** ocorrências do mesmo anti-pattern viram um único bloco com várias linhas. Se o mesmo anti-pattern ocorrer em domínios bem diferentes (ex.: secret de app e credencial SMTP), pode separar em dois blocos.
6. **Recommendation acionável:** diga o que fazer e para onde mover (`mover para src/models/produto_model.py com placeholders ?`) e referencie o padrão do playbook.
7. **Deprecated APIs:** seção sempre presente, mesmo vazia.
8. **Endpoint Inventory:** todas as rotas da Fase 1. É a base da validação da Fase 3.
9. **Mínimo esperado:** um projeto legado típico tem pelo menos 5 findings. Se encontrar menos, refaça a varredura com o checklist do catálogo antes de concluir.
10. **Nada de escrita em disco:** o relatório é impresso na conversa. A pergunta final é a última linha da resposta.

## Exemplo de finding bem escrito

```
### [CRITICAL] SQL Injection (AP-01)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155-166, 174, 188, 192, 220, 224, 279-281, 289-297
Description: Queries montadas por concatenação de strings com valores do request, ex.: "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'" em login_usuario.
Impact: Permite bypass de login (' OR '1'='1), leitura e destruição de qualquer tabela.
Recommendation: Usar placeholders "?" com tupla de parâmetros em todas as queries dos novos models (Playbook P-01).
```

## Exemplo de finding mal escrito (não faça)

```
### [HIGH] Código desorganizado
File: models.py
Description: O código está bagunçado.
```

Falhas: sem ID do catálogo, sem linhas, descrição genérica, sem impacto nem recomendação.
