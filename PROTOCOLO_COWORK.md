# PROTOCOLO DE TRABALHO — Ant's

**Este arquivo é um contrato.** Qualquer inteligência artificial que for manusear este
repositório — Claude, Claude Code, ChatGPT, Copilot, ou qualquer outra — deve ler este
documento antes da primeira alteração e seguir o que está aqui.

O dono do projeto é **Jonas**. Ele cola este arquivo no início de cada sessão porque
nenhuma IA tem memória entre conversas. O compromisso não vive na memória do assistente:
**vive aqui, versionado junto com o código.**

**Versão do protocolo:** 1.0 · **Criado em:** 17/08/2026 · **Base:** commit `f94edf8` (9.3)

---

## 1. Por que este protocolo existe

O problema que ele resolve, nas palavras do dono:

> "Eu converso com a IA, ela me mostra ferramentas. O Code aplica no meu projeto de forma
> eficaz. Mas eu não consigo ver quais são as reais mudanças no projeto. Falta transparência
> entre o que eu estou construindo e o que está sendo construído."

Este projeto já tem uma tradição de honestidade técnica, visível nos próprios arquivos:
`AUDITORIA_HONESTIDADE_9.0.md`, `DIAGNOSTICO_10_PERGUNTAS.md`, `SEGURANCA_9.3.md`.
Painéis que mostravam dado sem fonte foram removidos em vez de preenchidos com enfeite.

**Este protocolo estende essa regra do código para o processo de trabalho.**

---

## 2. As seis regras

### Regra 1 — Diagnóstico antes de correção

Nenhuma alteração entra sem que exista, antes dela, uma **medição** que a justifique.
"Parece que o problema é X" não basta. Reproduza, meça, registre o número.

Se a hipótese não se confirmar na medição, **diga isso** e continue procurando. Uma
hipótese derrubada por experimento é progresso, não fracasso.

### Regra 2 — Prova executável, não descrição

Toda mudança relevante vem acompanhada de algo que o dono possa **abrir e conferir**:
captura de tela real, artefato HTML interativo, saída de comando, número antes/depois.

Não é aceitável entregar apenas a frase "corrigido". O dono precisa ver.

### Regra 3 — A rede de segurança é sagrada

```
pytest -q  →  deve terminar em "passed", sem falha
```

Rodar **antes** e **depois** de cada tarefa. Quem adiciona teste declara o novo total.
Quem quebra um teste conserta ou reverte — não segue adiante.

Contagem na criação deste protocolo: **534 passed**.

### Regra 4 — Um commit por tarefa

Nada de commit-monstro. Se algo quebrar, tem que ser possível identificar qual mudança
causou. Formato:

```
<versão> · <Tarefa>: <o que mudou>

Diagnóstico: <a medição que motivou>
Correção:    <o que foi feito>
Prova:       <medição antes → depois>
Testes:      <N> passed (sem regressão)
```

### Regra 5 — Declarar o que NÃO foi verificado

**Esta é a regra mais importante do protocolo.**

Todo relatório termina com uma seção "O que não foi verificado". Nela entram: hipóteses
não confirmadas, ambientes não testados, limites do ambiente de quem executou, e
qualquer coisa que ficou de fora.

Omitir limite é o mesmo que mentir. Um assistente que entrega só a parte boa está
vendendo, não fazendo engenharia.

### Regra 6 — Interface nunca inventa texto

Herdada da auditoria 9.0 e agora obrigatória para todo código novo de front-end:

- Painel sem fonte de dado real **não é preenchido com texto de exemplo** — ou mostra
  dado verdadeiro, ou declara honestamente que não há dado
- Rótulo como "ao vivo" ou "tempo real" só pode existir se o conteúdo for, de fato, ao vivo
- Estado vazio se explica: "nenhum bot ativo", não silêncio

**Caso real que motivou esta regra:** o modal `#bot-vision-modal` existia no `index.html`
com os campos "Ação atual: Buscando fontes primárias sobre o tema…" e "Log em tempo real",
mas nenhum JavaScript o alimentava. O texto era fixo, igual para todo bot, em toda missão.
Parecia vivo; não era. Foi substituído pela Câmera ao Vivo (`web/js/bot_camera.js`), que
só exibe evento real.

---

## 3. O que entregar ao fim de cada tarefa relevante

Cinco itens. Sempre os cinco.

| # | Entrega | Formato |
|---|---|---|
| 1 | **Artefato de prova** | HTML interativo, captura de tela ou saída de comando |
| 2 | **Relatório de consulta externa** | `.md` autossuficiente, com perguntas específicas |
| 3 | **Ordem de serviço de execução** | `.md` com caminho, linha, patch e critério de aceite |
| 4 | **Melhorias recomendadas** | O que o profissional faria a seguir, e por quê |
| 5 | **O que não foi verificado** | Os limites explícitos da entrega |

"Tarefa relevante" = qualquer coisa que altere comportamento, corrija defeito, adicione
funcionalidade ou mude arquitetura. Ajuste de texto não conta.

---

## 4. Estado do projeto (atualizar a cada entrega)

| Item | Valor |
|---|---|
| Versão | 9.4 em desenvolvimento (branch `ants-9.4-refino`, base 9.3 `f94edf8`) |
| Testes | **549 passando** (base 9.3 era 529 no `main`; +20 no 9.4) |
| Serviço oficial no Render | **`ants-yeys`** (roda o commit `d0b5510`, versão 9.2) |
| Serviços duplicados | 7 outros, mesmo repositório, plano gratuito |
| Objetivo principal do dono | **usar o projeto no computador** |

### Entregue no 9.4 (branch `ants-9.4-refino`)

T0 protocolo versionado · T-A sidebar fixa · T1/T-C responsivo (390: 98→0 cortes) ·
T-B memória automática (auto-recall + auto-sono; busca manual oculta, IDs legados
preservados) · T2 Câmera ao Vivo (bot_camera.js/css; 5 bots reais em ordem; fim do
modal de texto fixo) · T3 selo de proveniência + "buscar de novo" (fim do cache
invisível) · T4 as 7 abas no celular · T5 WebSocket primário + polling fallback
(fim do polling de 600ms) · T6 saúde numa fonte só · T7 LocalProvider sem urllib ·
T8 contador de testes real · T9 zero emoji no JS editável (legados via noEmojiLayer) ·
FASE 4 SW bump por release.

### Pendências abertas

1. **Tela branca no `ants-7ylk`** — sem diagnóstico. O servidor responde `200 OK`, o mesmo
   commit roda perfeitamente em ambiente local. A causa é do lado do navegador. Falta o
   console do aparelho afetado. (Teste barato ainda não feito: abrir em aba anônima do
   celular — se funcionar, é SW com cache velho; o bump do 9.4 tende a resolver.)
2. **Token de segurança não configurado** — a guarda do 9.3 só age com `ANTS_PUBLIC=1` e
   `ANTS_API_TOKEN` definidos. Hoje o `/health` responde `"mode": "open"`. Ação do dono.
3. ~~Cache de respostas invisível~~ — **RESOLVIDO no 9.4 (T3)**: o selo declara "da memória
   (repetida)" e oferece "buscar de novo" (força o pipeline, ignorando o cache).
4. **Sem servidor MCP** — não há implementação do protocolo no repositório. (Recomendação
   futura no RELATORIO_PARA_CHATGPT; adaptador opcional, sem tornar o Ant's dependente.)

---

## 5. Restrições que toda recomendação deve respeitar

- **Plano gratuito do Render**: 512 MB de RAM, um worker, hibernação por inatividade
- **Front-end sem build step** — JS puro, sem webpack, sem npm no fluxo do front
- **Sem framework de UI** — migrar para React/Vue seria reescrita, não melhoria
- **Custo zero é requisito**, não meta
- **Docker + Render** é o alvo de deploy
- **534 testes** são intocáveis

---

## 6. Como usar este arquivo numa sessão nova

Cole, no início da conversa:

> Leia o `PROTOCOLO_COWORK.md` do repositório antes de qualquer coisa e siga as seis
> regras. Confirme que leu listando as seis, e me diga o estado atual das pendências
> abertas antes de propor qualquer mudança.

Se o assistente não conseguir listar as seis regras, ele não leu — não deixe avançar.

---

## 7. Histórico

| Data | Versão | Mudança |
|---|---|---|
| 17/08/2026 | 1.0 | Criação. Auditoria de 8 achados, correção de celular verificada (98 → 0 elementos cortados), Câmera ao Vivo implementada substituindo o modal de texto fixo. |
