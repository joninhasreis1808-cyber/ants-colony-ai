# O serviço único, final e totalmente funcional — Ant's 9.14

Objetivo: analisar os 8 serviços Render, avaliar cada um, e consolidar tudo o que
construímos **desde o início** num **único serviço** claro, seguro e funcional em
todas as suas capacidades.

## 1 · Avaliação dos 8 serviços (estado real)

Cada serviço estava **congelado no commit de quando foi criado** — o webhook
GitHub→Render nunca disparou auto-deploy, apesar de `autoDeployTrigger: commit`.
Só o `ants-7ylk` foi levado ao código atual (deploy manual via API).

| Serviço | URL | Versão congelada | Decisão |
|---------|-----|------------------|---------|
| **ants-7ylk** | https://ants-7ylk.onrender.com | **9.14 (atual)** | ✅ **MANTER — serviço final** |
| ants (aqu1) | https://ants-aqu1.onrender.com | 6.0 (`beb751b`) | ❌ apagar |
| ants-uoat | https://ants-uoat.onrender.com | 6.0 (`2a46621`) | ❌ apagar |
| ants-xt89 | https://ants-xt89.onrender.com | 7.x (`7a665ed`) | ❌ apagar |
| ants-1c3s | https://ants-1c3s.onrender.com | 7.2 (`c12fde3`) | ❌ apagar |
| ants-y1sj | https://ants-y1sj.onrender.com | 9.0 (`d688028`) | ❌ apagar |
| ants-8qb4 | https://ants-8qb4.onrender.com | 9.1 (`5ce207e`) | ❌ apagar |
| ants-yeys | https://ants-yeys.onrender.com | 9.2 (`d0b5510`) | ❌ apagar |

Todos rodam Docker, plano free, região Oregon, `healthCheckPath: /health`.

## 2 · O serviço final: `ants-7ylk`

- **URL:** https://ants-7ylk.onrender.com
- **Código:** `main` (cumulativo — inclui **todas** as fases, da v6.0 à 9.14).
- **Saúde:** o Render só marca o deploy como `live` depois que `/health`
  responde 200; portanto `live` = a colônia inteira está servindo.

O código em `main` é **cumulativo**: uma versão nova nunca remove a anterior.
Logo, o serviço no commit atual já contém **tudo o que criamos desde o início**.

## 3 · O que "tudo desde o início" inclui (as partes, juntas)

| Camada | Capacidade | Estado no serviço |
|--------|-----------|-------------------|
| Núcleo | 5 castas + Mente Colmeia, EventBus, memória (LTM), PWA offline | ✔ |
| Percepção/Ação | perceber, ação de arquivo/app, device com escopos | ✔ (ação sensível gated) |
| Segurança 9.3 | guarda do dono (token), `path_guard`, postura no `/health` | ✔ |
| Córtex 9.5 | raciocínio plugável (rules › Ollama › API), sem vazar chave | ✔ (rules em prod) |
| Inteligência B | Cartógrafa, planejador hierárquico, crítica, experiência viva | ✔ |
| Superorganismo C | decisão coletiva (quórum), atenção (estigmergia), labor adaptativo | ✔ |
| Ferramentas D | ToolRegistry + Scope Guard (compute, arquivos), gated | ✔ |
| Autonomia E | laço Observar→Planejar→Agir→Verificar com governador | ✔ |
| Interface F | Câmera ao Vivo, painel da Mente, console de missão | ✔ |
| Evolução H | propor→aprovar→aplicar (só dados, nunca código) | ✔ (gated) |
| Missão AGE (9.12) | a missão usa ferramentas de verdade (12×12 → 144) | ✔ |
| Persistência (9.13) | histórico de missões + experiência + evolução em disco | ✔ código (opt-in) |
| Desbloqueio (9.14) | dono desbloqueia rotas gated no navegador (X-Ants-Token) | ✔ |

## 4 · Público, funcional **e** seguro (9.14)

O design é *fail-closed* (a coleira do dono): num deploy público as rotas que
mudam estado — `/evolution/*`, `/tools/run` — exigem o token do dono. As rotas de
missão e as perguntas seguem **abertas**, então a PWA funciona para qualquer
visitante.

Para o **dono** usar as rotas gated pela web, o `api_bridge` agora manda a chave
do dono como `X-Ants-Token` (guardada só no navegador dele, em `localStorage`). No
console há o campo **"Chave do dono → Desbloquear"**. Visitante anônimo não manda
chave e continua barrado.

Configuração do serviço final:
- `ANTS_PUBLIC=1` — declara exposição pública (o `/health` mostra `publico:true`).
- `ANTS_API_TOKEN=<segredo>` — o token que o dono cola no campo "Desbloquear".

## 5 · Persistência em produção (honesto)

No plano **free** o disco é efêmero: `ANTS_STATE_DIR` não está setado, então o
histórico de missões fica em memória e reinicia a cada redeploy/hibernação. O
código de persistência está pronto — basta, quando quiser, adicionar um disco
(plano pago) e setar `ANTS_STATE_DIR` para o histórico sobreviver.

## 6 · Para deixar UM só serviço (ação no dashboard)

Não há API/ferramenta para **apagar** serviços — só pelo dashboard. Mantenha o
`ants-7ylk` e apague os 7 abaixo (Settings → Delete Service):

- ants → https://dashboard.render.com/web/srv-d9b6c7reo5us73e1cbcg
- ants-uoat → https://dashboard.render.com/web/srv-d9b71ireo5us73e2msbg
- ants-xt89 → https://dashboard.render.com/web/srv-d9gba3ernols73c9h9o0
- ants-1c3s → https://dashboard.render.com/web/srv-d9hnu8jrjlhs739f5vt0
- ants-y1sj → https://dashboard.render.com/web/srv-d9saldnavr4c73arua00
- ants-8qb4 → https://dashboard.render.com/web/srv-d9sav47avr4c73asjcag
- ants-yeys → https://dashboard.render.com/web/srv-d9v1tvvlk1mc73bdddog

**Manter:** ants-7ylk → https://dashboard.render.com/web/srv-d9vosapt0dsc73e5p0k0
