/* Ant's — live_dashboard.js: visão organizacional (hierarquia) + biológica
   (rede viva) da colônia.

   Achado declarado sem corrigir ao investigar o item 6 (Repertório da
   Colmeia v2): este módulo desenhava um "COLONY" fixo no código, com
   números de "ativas/total" por casta que nunca vieram de lugar nenhum —
   pura decoração fingindo ser telemetria viva. Viola a mesma regra que já
   vale para o resto do app (ESTADO_ATUAL.md §6: "qualquer falha de
   endpoint mostra 'colônia adormecida' e '—' — nunca números falsos").

   Corrigido: as 6 castas-base (estrutura) são as mesmas reais de
   backend/hivemind/castes_base.py — isso é fato do sistema, não dado.
   A CONTAGEM por casta vem de GET /hive/formations (mesma fonte que o
   painel de formações da Cognição usa), somando os bots das formações
   ainda em curso (forming/running — "done" já entregou, não conta como
   atividade agora). Sem resposta da rede: "sem dados", nunca um zero
   fingindo ser uma contagem confirmada. */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);

  // As 6 castas-base reais — mesma lista/ícones que formations_panel.js
  // usa para os bots dentro de cada formação (consistência entre abas).
  const CASTES = [
    { key: "exploradores", label: "Exploradoras", role: "busca · descoberta", icon: "i-compass" },
    { key: "construtores", label: "Construtoras", role: "constrói · conserta", icon: "i-cpu" },
    { key: "coletores", label: "Coletoras", role: "compila · envia à colmeia", icon: "i-book" },
    { key: "costureiros", label: "Costureiras", role: "interliga memórias", icon: "i-colony" },
    { key: "operarias", label: "Operárias", role: "ação no dispositivo", icon: "i-worker" },
    { key: "soldados", label: "Soldados", role: "crítica · verificação", icon: "i-shield" },
  ];
  // Rainha: não é uma casta de formação (não tem contagem em /hive/formations)
  // — é a orquestradora, sempre presente. Fato estrutural, não dado a inventar.
  const RAINHA = { key: "rainha", label: "Rainha", role: "coordenação · objetivos", icon: "i-crown" };

  function api() { return window.AntAPI; }

  // Soma bots reais por casta nas formações ainda em curso. null = "não
  // sei" (rede indisponível) — nunca confundir com zero.
  async function fetchCounts() {
    if (!api()) return null;
    try {
      const d = await api().get("/hive/formations");
      const forms = (d && d.formations) || [];
      const counts = {};
      CASTES.forEach((c) => { counts[c.key] = 0; });
      forms.forEach((f) => {
        if (f.status === "done") return;
        const fc = f.counts || {};
        Object.keys(fc).forEach((k) => { if (k in counts) counts[k] += fc[k]; });
      });
      return counts;
    } catch (e) { return null; }
  }

  function hierarchyRow(c, count) {
    const cnt = count == null
      ? '<span class="cr-count" style="color:var(--dim)">sem dados</span>'
      : count > 0
        ? '<span class="cr-count"><b>' + count + '</b> agora</span>'
        : '<span class="cr-count" style="color:var(--dim)">nenhuma agora</span>';
    return '<div class="caste-row caste-' + c.key + '" style="--cc:var(--caste)">' +
      '<span class="cr-ico"><svg class="ico"><use href="#' + c.icon + '"/></svg></span>' +
      '<span><div class="cr-name">' + c.label + '</div><div class="cr-role">' + c.role + '</div></span>' +
      cnt + '</div>';
  }

  // Rainha nunca tem contagem de bots (não é uma casta de formação) — não
  // reaproveita "sem dados" (isso significaria falha de rede, não é o caso).
  function rainhaRow() {
    return '<div class="caste-row caste-rainha" style="--cc:var(--caste)">' +
      '<span class="cr-ico"><svg class="ico"><use href="#' + RAINHA.icon + '"/></svg></span>' +
      '<span><div class="cr-name">' + RAINHA.label + '</div><div class="cr-role">' + RAINHA.role + '</div></span>' +
      '<span class="cr-count" style="color:var(--dim)">sempre presente</span></div>';
  }

  function renderHierarchy(el, counts) {
    const rows = [rainhaRow()]
      .concat(CASTES.map((c) => hierarchyRow(c, counts ? counts[c.key] : null)));
    el.innerHTML = rows.join("");
  }

  function renderNetwork(el, counts) {
    const W = el.clientWidth || 320, H = 240, cx = W / 2, cy = H / 2;
    const svg = ['<svg viewBox="0 0 ' + W + ' ' + H + '" style="width:100%;height:240px">'];
    const nodes = [RAINHA].concat(CASTES);
    const pts = nodes.map((c, i) => {
      const ang = ((i - 1) / CASTES.length) * Math.PI * 2 - Math.PI / 2;
      const r = i === 0 ? 0 : 88;
      return { x: cx + Math.cos(ang) * r, y: cy + Math.sin(ang) * r, c: c, n: i === 0 ? null : (counts ? counts[c.key] : null) };
    });
    // conexões da rainha (centro) a cada casta — "transmitting" só quando
    // sabemos de verdade que há bots atuando ali agora.
    pts.forEach((p, i) => {
      if (i === 0) return;
      const t = p.n > 0 ? " transmitting" : "";
      svg.push('<line class="colony-link' + t + '" x1="' + pts[0].x + '" y1="' +
        pts[0].y + '" x2="' + p.x + '" y2="' + p.y + '"/>');
    });
    pts.forEach((p, i) => {
      const isQueen = i === 0;
      const known = p.n != null;
      const st = isQueen ? "" : (!known || p.n === 0 ? " idle" : "");
      const rad = isQueen ? 15 : 11 + (known ? Math.min(p.n, 6) * 2 : 0);
      svg.push('<circle class="colony-node caste-' + p.c.key + st + '" cx="' + p.x +
        '" cy="' + p.y + '" r="' + rad + '"/>');
    });
    svg.push("</svg>");
    el.innerHTML = svg.join("");
  }

  async function mount(hierId, netId) {
    const h = $(hierId), n = $(netId);
    if (!h && !n) return;
    const counts = await fetchCounts();
    if (h) renderHierarchy(h, counts);
    if (n) renderNetwork(n, counts);
  }

  function isColonyTabOpen() {
    return !!document.querySelector("#tab-colony.is-active, #tab-colony.active");
  }
  function autoMount() { mount("colony-hierarchy", "colony-network"); }

  document.addEventListener("ants:tab", (e) => { if (e.detail === "colony") autoMount(); });
  document.addEventListener("ants:task-done", () => setTimeout(autoMount, 300));
  setInterval(() => { if (isColonyTabOpen()) autoMount(); }, 6000);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", autoMount);
  else autoMount();

  window.AntDashboard = { mount, CASTES };
})();
