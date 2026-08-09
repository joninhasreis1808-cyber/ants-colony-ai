# Ant's — Onde roda (alcance honesto por dispositivo)

> Regra: **não prometer o impossível.** Conversar e buscar funciona em todo
> lugar com internet; **agir no aparelho** depende do que cada sistema permite.

## Conversar + buscar conhecimento = **todos os dispositivos**
A busca web (Wikipedia → DuckDuckGo → SearXNG/Tavily/Brave se houver chave) e o
raciocínio/cálculo funcionam em qualquer aparelho com navegador e internet —
não há modelo de linguagem embutido (por isso roda até em celular/PC fraco).

## Instalar como app (PWA)
- **Android / Chrome / Edge (desktop):** "Instalar app" (manifest + service
  worker prontos). Abre em janela própria, funciona offline para o que é local.
- **iPhone (Safari):** Compartilhar → **Adicionar à Tela de Início**. Instala
  como PWA — serve para **conversar e buscar** (o iOS não dá controle de
  device a apps de terceiros).

## Agir no aparelho (arquivos/apps/mouse) = **só onde o SO permite**
| Plataforma | Ler pastas autorizadas / abrir apps-URLs | Mover/apagar arquivos | Controlar mouse/teclado |
|-----------|:---:|:---:|:---:|
| **PC (Windows/macOS/Linux)** — app nativo ou uvicorn local com `ANTS_RUNTIME=native` | ✅ | ✅ (com confirmação) | ✅ (app nativo empacotado) |
| **Android** | limitado (via app nativo/Termux; escopos restritos) | limitado | ✗ (Android bloqueia) |
| **iPhone** | ✗ | ✗ | ✗ |
| **Web (Render)** | ✗ (só planeja) | ✗ | ✗ |

Sempre atrás de **permissão explícita** (nenhum escopo por padrão), whitelist de
pastas, confirmação para ações destrutivas e botão de pânico.

## Responsivo
Layout adapta a celular (bottom-nav), tablet e desktop; alvos de toque ≥48px.

## Honestidade
Se a busca falhar (sem rede), a colônia **declara** — não inventa. Se uma
capacidade não existe numa plataforma, o selo de runtime diz. Nunca fingimos
suporte universal.
