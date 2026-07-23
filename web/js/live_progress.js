/* Ant's — live_progress.js (7.2 · Bloco A): progresso VIVO no chat único.
 * Estilo assistente: cada etapa REAL aparece conforme acontece (ícone da
 * fase + bot + o que fez), com spinner → check; ao concluir, colapsa num
 * resumo clicável ("N etapas · N castas · confiança X · ver detalhes").
 * Fonte: os eventos reais que api_bridge já lê de /hive/status (ants:task-tick
 * / ants:task-done). Não toca nos 4 JS legados. Zero emoji (só SVG). */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c];
    });
  };
  // Fase real do evento → ícone SVG + casta (mesma identidade visual).
  var ICON = { plan: "i-crown", do: "i-compass", check: "i-shield",
               act: "i-check" };
  var CASTE = { plan: "caste-queen", do: "caste-explorer",
                check: "caste-soldier", act: "caste-worker" };

  function box() {
    var b = $("live-progress");
    if (!b) return null;
    return b;
  }

  function render(events, done, result) {
    var b = box(); if (!b) return;
    b.classList.add("show");
    var evs = (events || []).filter(function (e) { return e && e.message; });
    if (!evs.length && !done) {
      b.innerHTML = '<div class="lp-row"><span class="lp-spin"></span>' +
        '<span class="lp-msg">a colônia acordou e está montando a formação…</span></div>';
      return;
    }
    var rows = evs.map(function (e, k) {
      var last = k === evs.length - 1;
      var ph = (e.phase || "do").toLowerCase();
      var mark = (!done && last)
        ? '<span class="lp-spin"></span>'
        : '<svg class="ico sm lp-ok"><use href="#i-check"/></svg>';
      return '<div class="lp-row ' + (CASTE[ph] || "caste-worker") + '">' +
        mark +
        '<svg class="ico sm lp-ph"><use href="#' + (ICON[ph] || "i-ant") + '"/></svg>' +
        '<span class="lp-bot">' + esc(e.bot || "colônia") + '</span>' +
        '<span class="lp-msg">' + esc(e.message) + '</span></div>';
    }).join("");
    if (done) rows += summary(evs, result);
    b.innerHTML = rows;
    b.scrollTop = b.scrollHeight;
  }

  function summary(evs, r) {
    r = r || {};
    var castes = {};
    evs.forEach(function (e) { if (e.bot) castes[e.bot] = 1; });
    var prov = r.provenance || {};
    var bits = [evs.length + " etapas",
                Object.keys(castes).length + " castas"];
    if (r.confidence != null) bits.push("confiança " + r.confidence);
    if (prov.source) bits.push("fonte: " + esc(prov.source));
    if (prov.web) bits.push(esc(prov.web));
    return '<button class="lp-summary" type="button">' +
      '<svg class="ico sm"><use href="#i-check"/></svg> ' +
      esc(bits.join(" · ")) + ' — ver detalhes</button>';
  }

  // clique no resumo: alterna a visão compacta/detalhada
  document.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest(".lp-summary");
    if (!btn) return;
    var b = box(); if (b) b.classList.toggle("collapsed");
  });

  document.addEventListener("ants:task-tick", function (e) {
    var d = e.detail || {}; var st = d.status || {};
    render(st.events || [], !!d.done, st.result || {});
  });
  document.addEventListener("ants:task-done", function (e) {
    var st = e.detail || {};
    render(st.events || [], true, st.result || {});
    var b = box(); if (b) b.classList.add("collapsed");
  });
})();
