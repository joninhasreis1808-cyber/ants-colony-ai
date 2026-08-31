/* Ant's — cognition_panel.js (9.25 · Cognição ao Vivo): a UI mostra a cognicao.
 * Consome o resultado real da missao (evento ants:task-done) — trilha tipada
 * (cognitive_trace), cadeia de fallback (degrau + se escalou ao humano) e modo —
 * e busca a CALIBRACAO viva (/calibration: ECE + confiabilidade). Nunca inventa:
 * sem dado, estado vazio honesto. Colapsavel (lembra a preferencia). Aditivo;
 * nao toca nos JS legados. Estilo escopado em web/css/live_cognition.css. */
(function () {
  "use strict";
  var LADDER = ["primary", "secondary", "cognitive", "human"];
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; });
  };
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }

  // Resumo puro do resultado da missao (facil de inspecionar/testar).
  function summarize(result) {
    var r = result || {};
    var trace = r.cognitive_trace || null;
    var fb = r.fallback || null;
    var mode = r.mode || (r.decision && r.decision.mode) || null;
    return {
      steps: trace && trace.steps ? trace.steps.length : 0,
      counts: trace && trace.counts ? trace.counts : {},
      reached: fb ? fb.reached : null,
      escalate: fb ? !!fb.escalate_human : false,
      mode: mode,
    };
  }

  function shell() {
    var el = document.getElementById("ants-cognition");
    if (el || !document.body) return el;
    el = document.createElement("div");
    el.id = "ants-cognition";
    el.setAttribute("data-collapsed", store("ants:cog-collapsed") === "1" ? "1" : "0");
    el.innerHTML =
      '<div class="lc-head"><span class="lc-dot"></span>' +
      '<span class="lc-title">Cognição ao Vivo</span>' +
      '<span class="lc-caret">▾</span></div>' +
      '<div class="lc-body"><div class="lc-muted">Aguardando a primeira missão…</div></div>';
    document.body.appendChild(el);
    el.querySelector(".lc-head").addEventListener("click", function () {
      var c = el.getAttribute("data-collapsed") === "1" ? "0" : "1";
      el.setAttribute("data-collapsed", c);
      el.querySelector(".lc-caret").textContent = c === "1" ? "▸" : "▾";
      store("ants:cog-collapsed", c);
    });
    return el;
  }

  function ladderHTML(reached, escalate) {
    if (!reached) return "";
    var idx = LADDER.indexOf(reached);
    var pills = LADDER.map(function (s, i) {
      return '<span class="lc-step" data-on="' + (i <= idx ? 1 : 0) + '">' + esc(s) + "</span>";
    }).join("");
    var warn = escalate ? '<span class="lc-chip warn">precisa de humano</span>' : "";
    return '<div class="lc-row"><span class="lc-label">Fallback</span>' +
           '<span class="lc-ladder">' + pills + "</span>" + warn + "</div>";
  }

  function renderCognition(box, s) {
    var counts = Object.keys(s.counts).map(function (k) {
      return '<span class="lc-tag">' + esc(k) + ":" + s.counts[k] + "</span>"; }).join(" ");
    var mode = s.mode ? '<div class="lc-row"><span class="lc-label">Modo</span><span class="lc-chip">' + esc(s.mode) + "</span></div>" : "";
    var body = box.querySelector(".lc-body");
    body.setAttribute("data-cog", "1");
    body.innerHTML =
      ladderHTML(s.reached, s.escalate) + mode +
      '<div class="lc-row"><span class="lc-label">Trilha</span><b>' + s.steps + "</b> passos</div>" +
      (counts ? '<div class="lc-tags">' + counts + "</div>" : "") +
      '<div class="lc-row" id="lc-calib"><span class="lc-label">Calibração</span><span class="lc-muted">—</span></div>';
    fetchCalibration(box);
  }

  function renderCalibration(box, data) {
    var row = box.querySelector("#lc-calib");
    if (!row) return;
    if (!data || !data.total) {
      row.innerHTML = '<span class="lc-label">Calibração</span><span class="lc-muted">sem amostras ainda</span>';
      return;
    }
    var ecePct = Math.round((1 - Math.min(1, data.ece)) * 100);   // 100% = bem calibrada
    row.innerHTML =
      '<span class="lc-label">Calibração</span>' +
      '<span>ECE ' + esc(data.ece) + ' · ' + data.total + ' amostras</span>' +
      '<div class="lc-bar" style="flex:1;min-width:80px"><i style="width:' + ecePct + '%"></i></div>';
  }

  function fetchCalibration(box) {
    try {
      fetch("/calibration").then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) { renderCalibration(box, d); })
        .catch(function () { /* offline/sem rota → mantem '—' honesto */ });
    } catch (e) { /* ambiente sem fetch */ }
  }

  function render(result) {
    var s = summarize(result);
    if (!s.steps && !s.reached) return;   // sem dado real → nao mostra nada novo
    var box = shell();
    if (box) renderCognition(box, s);
  }

  window.AntCognition = { summarize: summarize, render: render };

  document.addEventListener("ants:task-done", function (e) {
    var st = e.detail || {};
    try { render(st.result || {}); } catch (err) { /* nunca derruba a UI */ }
  });
})();
