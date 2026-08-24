# Verificação de produção — Ant's 9.15 (ants-c2ik)

Prova real, colhida do serviço no ar em **https://ants-c2ik.onrender.com/health**
(deploy manual do commit 9.15). Confirma que o código cumulativo — de tudo desde o
início até o poder de ação 9.15 — está servindo em produção.

## O que o /health provou
- `version: 2.0.0`, `status: healthy`, `modules.planning: true`.
- `intelligence.mission_endpoint: /mission` e `evolution_endpoint: /evolution` — a
  camada Manus está exposta.
- `intelligence.tools` inclui **`write_file`** (o poder de ação 9.15 no catálogo);
  `available:false` porque o escopo `write_files` só é concedido pelo dono.
- `intelligence.cartographer`: 7 rotas (computation → device_action).
- `reasoning.backend: rules` — cérebro determinístico honesto (sem LLM externo).
- `providers: [wikipedia, duckduckgo]` — busca web real disponível quando online.
- `tests: 0` — **esperado** em produção (a pasta `tests/` não vai na imagem enxuta;
  o front mostra "—", nunca um número inventado).

## Item em aberto (autenticação do dono)
`auth: {mode: "open", token_configurado: false, publico: false}` — este serviço
(novo slug, criado na reconexão) ainda **não tem** as variáveis de ambiente. Sem
elas: missões e perguntas funcionam; Evolução/Ferramentas ficam trancadas. Para
ligar o desbloqueio do dono, definir no serviço:
- `ANTS_PUBLIC=1`
- `ANTS_API_TOKEN=<segredo do dono>`

e colar o token em "Chave do dono → Desbloquear" no console.

## Propósito duplo deste commit
Além de registrar a verificação, serve de **teste do auto-deploy**: se o GitHub App
do Render já tem acesso ao repositório, o merge deste commit no `main` deve disparar
um deploy automático em ants-c2ik com trigger "Push to main" (não mais
`blueprint_sync`).

## Auto-deploy ativado (via Deploy Hook)
O webhook nativo GitHub→Render não disparava (mesmo com o repo vinculado). Solução
confiável, sem OAuth/GitHub App: o workflow `.github/workflows/deploy.yml` já
buildava a imagem e fazia smoke test do `/health` a cada push no `main`; agora,
com o segredo `RENDER_DEPLOY_HOOK` configurado, o passo final faz `POST` no Deploy
Hook do Render — o deploy só acontece **depois** de o build e o `/health` passarem.
Este commit é o teste: o merge no `main` deve disparar o deploy sozinho (trigger
"Deploy Hook", não `blueprint_sync`).

<!-- Snapshot bruto do /health (produção), para auditoria -->
```json
{"status":"healthy","version":"2.0.0","bots_active":5,"tasks_submitted":9,
 "providers":["wikipedia","duckduckgo"],"tests":0,
 "reasoning":{"backend":"rules","llm":false,"model":null},
 "intelligence":{"hierarchical_planner":true,"collective_decision":true,
   "autonomous_loop":true,"controlled_evolution":true,
   "mission_endpoint":"/mission","evolution_endpoint":"/evolution"},
 "auth":{"mode":"open","token_configurado":false,"publico":false}}
```
