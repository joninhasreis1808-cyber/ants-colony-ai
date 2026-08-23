# Auto-avaliação profissional — Ant's 9.13

**Data:** 2026-08-23
**Escopo:** verificação verdadeira, de ponta a ponta, de todas as funções e
capacidades da colônia — não checagem de import, mas exercício real de cada
comportamento (endpoint ou módulo) comparando **esperado × real**.

## Método

Foi construído um arnês de auditoria que roda o comportamento real de cada
capacidade e afirma o resultado esperado. Depois de validado, ele foi convertido
numa **suíte de testes viva** (`tests/test_full_audit_913.py`, 16 testes) para
que qualquer regressão apareça no CI — não num relatório pontual.

- **Total da suíte:** 704 passando, 5 skipped.
- **Auditoria dedicada:** 22/22 capacidades OK.

## Resultado por capacidade

| # | Capacidade | Prova executada | Resultado |
|---|------------|-----------------|-----------|
| 1 | Keep-alive `/ping` | responde `{"pong":"ok"}` | ✔ |
| 2 | `/health` completo | status, módulos, inteligência, córtex, auth, nº de testes real | ✔ |
| 3 | Catálogo `/tools` | 6 ferramentas (compute + arquivos) | ✔ |
| 4 | Execução gated `/tools/run` | compute `12*12 = 144`, Scope Guard valida antes | ✔ |
| 5 | `path_guard` (blacklist) | `read_file /etc/passwd` recusado mesmo autorizado | ✔ |
| 6 | Missão AGE com ferramenta | `/mission/run` → rota computation → usa compute → **144** | ✔ |
| 7 | Histórico persistível | `/mission` lista; `/mission/{id}` devolve desfecho | ✔ |
| 8 | Laço autônomo | `/mission/auto` converge (consenso das castas) → **42** | ✔ |
| 9 | Decisão coletiva route-aware | determinístico→comprometer; evidência-sem-fonte→investigar | ✔ |
| 10 | Guarda de objetivo (drift) | cálculo não marca desvio falso | ✔ |
| 11 | Campo de atenção (estigmergia) | foco reforçado e ranqueado | ✔ |
| 12 | Divisão de trabalho adaptativa | investigar → realoca bots ao gargalo | ✔ |
| 13 | Governador de autonomia | laço nunca excede o teto de ciclos | ✔ |
| 14 | Memória de experiência (viés) | sucesso repetido promove a rota | ✔ |
| 15 | Evolução controlada | minerar → aprovar → aplicar (só dados, nunca código) | ✔ |
| 16 | Persistência opt-in | `missions.json` + `mission_outcomes.json` gravam e recarregam | ✔ |
| 17 | Córtex plugável | backend honesto ∈ {rules, ollama, api} | ✔ |
| 18 | Pesquisa profunda offline | conclui sem inventar fatos | ✔ |
| 19 | Blackboard | snapshot coeso das chaves da missão | ✔ |
| 20 | Cartógrafa | 7 rotas conhecidas | ✔ |
| 21 | Planejador hierárquico | monta TaskGraph topológico por rota | ✔ |
| 22 | PWA na raiz | `index.html` servido com scripts aditivos | ✔ |

## Honestidade sobre as falhas iniciais

A primeira passada acusou 4 "falhas". Investigando cada uma contra a API real do
código, **nenhuma era defeito de produto** — eram suposições erradas do próprio
arnês de auditoria:

1. **compute** — a resposta vem em `result.answer` (o registro embrulha o
   resultado). O arnês lia `answer` na raiz. Comportamento do produto: correto.
2. **decisão coletiva** — o veredito é em português (`comprometer`/`investigar`);
   o arnês comparava com `commit`/`investigate`. Produto: correto.
3. **governador** — `AutonomyGovernor` é um *dataclass* de limites (teto de
   ciclos + prazo); o laço é quem os aplica em `run_autonomous_mission`. O arnês
   chamava um método inexistente. Produto: correto.
4. **pesquisa profunda** — mora em `backend.hivemind.deep_research` e recebe um
   `Task`, escrevendo os achados na memória. O arnês usava um caminho/assinatura
   inexistentes. Produto: correto.

A correção foi feita **no arnês**, para casar com o comportamento real e correto
— jamais afrouxando asserção para "passar". As melhorias de robustez que
acompanharam (persistência tolerante a snapshots ricos via `default=str`; teto do
histórico para o disco não crescer sem limite) foram aplicadas no código de
produção e cobertas por teste.

## Conclusão

A colônia faz o que promete, de ponta a ponta, e agora se auto-avalia no CI. Não
há nenhum defeito aberto. Próximo passo: deploy.
