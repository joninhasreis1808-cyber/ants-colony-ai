# Ant's — Inventário de funcionalidades (o que a IA sabe fazer hoje)

> Tudo que o cérebro já entrega, com o endpoint correspondente — para a nova
> interface saber o que pode expor. Cada linha existe e foi verificada no
> backend em execução. "Onde" = server (roda em qualquer deploy) ou native
> (só no app nativo/local com `ANTS_RUNTIME=native`).

## 1 · Responder (o núcleo do chat)
| Capacidade | Como | Endpoint | Onde |
|-----------|------|----------|------|
| Enviar objetivo e receber resposta com trajeto | pipeline de bots P-D-C-A | `POST /hive/task` → `GET /hive/status/{id}` | server |
| Acompanhar ao vivo (empurrado) | SSE / WebSocket | `GET /hive/status/{id}/stream` · `WS /hive/live/{id}` | server |
| Cálculo exato (aritmética, raiz, %, potência) | córtex determinístico (SymPy, sem `eval`) | via `/hive/task` (intent computa) · `POST /perceive/equation` | server |
| Busca em cascata direta | memória→seed→curada→web→raciocínio | `POST /hive/search` | server (web real só fora do sandbox) |
| Raciocínio próprio honesto (9 camadas) | hipóteses, lacunas, confiança | `POST /mind/think` · `/reason` · `/assess` · `/infer` | server |
| Proveniência de cada resposta | `result.provenance.source` | em todo `result` | server |

## 2 · Aprender e melhorar com o tempo
| Capacidade | Endpoint | Onde |
|-----------|----------|------|
| Ensinar um fato ("Aprender isto") | `POST /hive/learn` | server |
| Recuperar o que aprendeu (cache/validade) | 2ª vez `cached:true` em `/hive/search`; memória em `/hive/task` | server |
| Memória de longo prazo (lembrar/recordar) | `POST /memory/remember` · `POST /memory/recall` | server |
| Consolidar/decair (ciclo de sono) | `POST /memory/sleep` | server |
| Saúde da memória (total, fortes, força média) | `GET /memory/health` | server |
| Feedback do usuário ajusta próximas respostas | `POST /organism/feedback` | server |

## 3 · Perceber (ler/ver/entender)
| Capacidade | Endpoint | Onde |
|-----------|----------|------|
| Entender texto (intenção, entidades, idioma) | `POST /perceive/text` | server |
| Resolver equação | `POST /perceive/equation` | server |
| Ler documento / imagem / OCR | `POST /perceive/document` · `/image` · `/ocr` | server (OCR precisa Tesseract) |
| Ler a tela por DOM e planejar ação | `POST /perceive/screen/dom` | server |
| Ler a tela por screenshot (OCR) | `POST /perceive/screen/image` | server |

## 4 · Agir no dispositivo (com segurança primeiro)
| Capacidade | Endpoint | Onde |
|-----------|----------|------|
| Selo de runtime (planeja vs. executa) | `GET /device/runtime` | server |
| Conceder/revogar escopos (7 escopos) | `GET/POST /device/scopes*` | server (efeito no native) |
| Autorizar pastas (whitelist + blacklist imutável) | `GET/POST /device/paths*` | server |
| Avaliar ação sem executar (gate + anti-injeção) | `POST /device/evaluate` | server |
| Criar/apagar arquivo (token + path_guard) | `POST /action/file` | native |
| Abrir/fechar app | `POST /action/app` | native |
| Navegar num site | `POST /action/navigate` | native (Playwright) |
| Aprovar/cancelar um plano de ação | `POST /hive/action/approve` · `/cancel` | server |
| Botão de pânico (congela + revoga) | `GET/POST /device/panic*` | server |
| Trilha de auditoria do device | `GET /device/audit` · `/audit/export` | server |

## 5 · Criar software (Factory)
| Capacidade | Endpoint |
|-----------|----------|
| Listar 6 modelos (api_rest, web_app, cli_tool, data_pipeline, saas_dashboard, mobile_app) | `GET /factory/templates` |
| Criar projeto a partir de descrição | `POST /factory/create` · `POST /factory/quick` |
| Listar / ver status de projetos | `GET /factory/projects` · `/projects/{id}` |
| Deploy de um projeto | `POST /factory/deploy/{id}` |

## 6 · Coordenação viva (castas, formações, enxame)
| Capacidade | Endpoint |
|-----------|----------|
| Formações da Rainha (criar/reforçar/liberar/concluir/descartar) | `GET/POST/DELETE /hive/formation*` |
| Enxame ao vivo (feromônios + estado por bot) | `GET /hive/swarm` |
| Cadeia "quem chamou quem" de uma tarefa | `GET /hive/recruitment/{id}` · `result.recruitment` |
| Feromônios / quórum / recomendação (bio) | `GET/POST /bio/*` |

## 7 · Estado e telemetria (painéis)
| Painel | Endpoint |
|--------|----------|
| Estado da colônia (respiração) | `GET /colony/state` |
| Sinais vitais / hormônios / circadiano | `GET /organism/vitals` |
| Capacidades reais (o que sei fazer agora) | `GET /organism/capabilities` |
| DNA / genoma / traços | `GET /organism/dna` |
| Tradições / cultura | `GET /organism/traditions` |
| Confiança (trust) por bot/estratégia | `GET /organism/trust` |
| Missões permanentes | `GET/POST /organism/missions` |
| Meta-cognição (gargalos, pesos) | `GET /colony/meta` |
| Observabilidade | `GET /colony/observability` |
| Autonomia (política) | `GET/POST /colony/autonomy` |
| Homeostase (regular por métricas do host) | `POST /colony/homeostasis` |
| Observador do host (duplicatas, backup, disco) | `GET /organism/observer` · `/observer/analyze` |
| Sistema imune (analisar ameaça de uma ação) | `POST /organism/immune/analyze` |
| Atividade / eventos do sistema nervoso | `GET /events/summary` · `/events/history` |
| Métricas Prometheus | `GET /metrics` |
| Saúde geral + postura de auth | `GET /health` |

## 8 · Segurança (9.3)
| Capacidade | Onde |
|-----------|------|
| Guarda de token nas rotas sensíveis (loopback aberto; público exige token) | `backend/api/security.py` |
| Postura honesta no `/health` (`auth.mode/token_configurado/publico`) | `GET /health` |
| 2ª guarda (path_guard) em `/action/file` | `POST /action/file` |
| Blacklist imutável de caminhos críticos | `POST /device/paths/allow` |
| Anti prompt-injection no gate de ação | `POST /device/evaluate` |

## O que a IA **não** faz (honestidade — não prometa na UI)
- **Não** embute LLM/rede neural pesada (decisão de projeto: rodar em qualquer
  device). Conhecimento de mundo vem de **busca web** + base curada.
- **Não** executa ações no device em modo **web** (`/device/runtime` diz
  `mode: web`): só **planeja**. Execução real só no app nativo.
- **Não** auto-modifica o próprio código em runtime (proibido por segurança).
- A **busca web real** depende de rede: no sandbox de captura ela dá `403`; a
  cascata então cai para cálculo/raciocínio/memória e **declara** isso.
