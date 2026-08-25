# Visão do Ant's — norte estratégico

Esta pasta guarda a **visão arquitetural de longo prazo** do Ant's (rumo a uma
plataforma de agente pessoal autônomo, com cérebro remoto + corpo local). É
**referência**, não uma ordem de implementação: nada aqui é feito "de uma vez" nem
por reescrita.

## Documentos

- **[`RELATORIO_MESTRE_7.0.md`](./RELATORIO_MESTRE_7.0.md)** — a visão completa
  (100 aprimoramentos, arquitetura remota×local, roadmap de 10 fases, o que NÃO
  fazer, e o ciclo completo da Mente Colmeia). Conteúdo curado pelo dono.
- **[`MAPA_ATUAL_x_VISAO.md`](./MAPA_ATUAL_x_VISAO.md)** — o mapa honesto do que o
  Ant's **já tem** (com os arquivos reais) × o que é **proposto**. Comece por aqui.
- **[`PROMPT_MESTRE_CLAUDE_CODE.md`](./PROMPT_MESTRE_CLAUDE_CODE.md)** — como
  conduzir a evolução com o Claude Code (engenheiro executor/revisor, não arquiteto
  sem limites) + a autoavaliação obrigatória de 15 perguntas ao fim de cada fase.

## Como usar (o fluxo cauteloso)

```text
1. Ler o MAPA (o que já existe)  →  2. Escolher UMA fronteira do Relatório
      ↓                                    ↓
5. Verificar + autoavaliação  ←  4. Incremento testado (encaixa no módulo atual)
      ↓                                    ↑
6. Promover (PR → CI → merge)  →  3. Proposta aprovada (finalidade, riscos, testes)
```

## Princípios inegociáveis

1. **Não reescrever.** A versão atual é o núcleo estável; evolução incremental e
   reversível. Incompatibilidade → **camada de compatibilidade**, nunca demolição.
2. **Núcleo próprio, offline-first.** Claude/n8n/APIs são ferramentas **opcionais**,
   jamais a inteligência fundamental.
3. **Cérebro remoto × corpo local.** O Render não controla o dispositivo sozinho —
   isso exige um **Local Agent** nativo, com ponte autenticada (capability tokens,
   comandos assinados). Nunca dar ao servidor acesso irrestrito à máquina.
4. **Segurança primeiro.** Capability-based permissions, path_guard, sandbox,
   auditoria, sistema imunológico; ações perigosas exigem consentimento.
5. **Honestidade.** Sem alucinação: evidência e proveniência; rotular
   verified/inferred/uncertain; autoevolução mexe só em **dados**, nunca em código
   de produção automaticamente.
6. **Interface reflete o real.** A IA atualiza a UI por **eventos/comandos
   tipados**, não editando HTML; animações representam estados verdadeiros.
7. **Todo passo testado.** MD5 dos 4 JS legados intocado; cada mudança com testes;
   cada fase encerra com a autoavaliação de 15 perguntas.

> Recomendação de partida do Relatório: o esqueleto (Task Graph + EventBus + Shared
> Blackboard + Tool Registry + Verifier + Checkpoint/Recovery) **já existe** no
> Ant's (ver o MAPA). O próximo passo natural é **padronizá-lo e conectá-lo** antes
> de abrir fronteiras novas como o Local Agent e a Browser Perception.
