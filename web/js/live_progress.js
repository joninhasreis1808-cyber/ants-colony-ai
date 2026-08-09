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
    if (prov.cached) bits.push("aprendido (memória)");
    if (prov.web) bits.push(esc(prov.web));
    return '<button class="lp-summary" type="button">' +
      '<svg class="ico sm"><use href="#i-check"/></svg> ' +
      esc(bits.join(" · ")) + ' — ver o trajeto</button>' + trace(r);
  }

  // Trajeto da missão: o que CADA bot fez, obstáculos e o que se aprendeu.
  function trace(r) {
    var t = r.trace; if (!t) return "";
    var parts = ['<div class="lp-trace">'];
    // Cadeia de raciocínio (9.1 · E): passos revelados quando existem.
    var chain = (r.provenance || {}).chain;
    if (chain && chain.steps && chain.steps.length) {
      parts.push('<div class="lp-th">Como cheguei nisso (raciocínio)</div>');
      chain.steps.forEach(function (s) {
        parts.push('<div class="lp-brow"><svg class="ico sm"><use href="#i-compass"/></svg>' +
          '<span>' + esc(s) + '</span></div>');
      });
    }
    parts.push('<div class="lp-th">Trajeto da missão — o que cada bot fez</div>');
    (t.bots || []).forEach(function (b) {
      var did = (b.did || []).slice(-3).map(esc).join(" · ") || "atuou";
      parts.push('<div class="lp-brow ' + (b.ok ? "" : "bad") + '">' +
        '<svg class="ico sm"><use href="#' + (b.ok ? "i-check" : "i-x") + '"/></svg>' +
        '<b>' + esc(b.bot) + '</b><span>' + did + '</span></div>');
    });
    if (t.errors && t.errors.length) {
      parts.push('<div class="lp-th">Obstáculos reais no caminho</div>');
      t.errors.forEach(function (e) {
        parts.push('<div class="lp-brow bad"><svg class="ico sm"><use href="#i-x"/></svg>' +
          '<b>' + esc(e.bot) + '</b><span>' + esc(e.detail) + '</span></div>');
      });
    }
    if (t.learnings && t.learnings.length) {
      parts.push('<div class="lp-th">O que a colônia aprendeu</div>');
      t.learnings.forEach(function (l) {
        parts.push('<div class="lp-brow"><svg class="ico sm"><use href="#i-book"/></svg>' +
          '<span>' + esc(l) + '</span></div>');
      });
    }
    if (t.conclusion) {
      parts.push('<div class="lp-th">Conclusão enviada ao chat</div>' +
        '<div class="lp-concl">' + esc(t.conclusion) + '</div>');
    }
    // "Aprender isto" (9.1 · D.2): consolida respostas boas da web/raciocínio.
    var src = (r.provenance || {}).source;
    if ((src === "web_search" || src === "reasoning") && t.conclusion) {
      parts.push('<button class="lp-learn" data-a="' + esc(t.conclusion) + '">' +
        '<svg class="ico sm"><use href="#i-book"/></svg> Aprender isto</button>');
    }
    parts.push("</div>");
    return parts.join("");
  }

  // "Aprender isto": consolida a resposta como memória (responde na hora depois)
  document.addEventListener("click", function (e) {
    var lb = e.target.closest && e.target.closest(".lp-learn");
    if (!lb || !window.AntAPI) return;
    var q = window.__antLastQuestion || "";
    window.AntAPI.post("/hive/learn", { question: q, answer: lb.dataset.a })
      .then(function () {
        lb.outerHTML = '<span class="lp-learned"><svg class="ico sm"><use href="#i-check"/></svg> Aprendido</span>';
      }).catch(function () {});
  });

  // clique no resumo: mostra/esconde o trajeto detalhado da missão
  document.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest(".lp-summary");
    if (!btn) return;
    var b = box(); if (b) b.classList.toggle("show-trace");
  });

  var lastTask = null;
  document.addEventListener("ants:task-tick", function (e) {
    var d = e.detail || {}; var st = d.status || {};
    // Nova missão: limpa o painel para não misturar com a anterior.
    if (d.taskId && d.taskId !== lastTask) {
      lastTask = d.taskId;
      var b = box(); if (b) { b.classList.remove("collapsed", "show-trace"); b.innerHTML = ""; }
    }
    render(st.events || [], !!d.done, st.result || {});
  });
  document.addEventListener("ants:task-done", function (e) {
    var st = e.detail || {};
    render(st.events || [], true, st.result || {});
    var b = box(); if (b) b.classList.add("collapsed");
  });
})();
