/* Ant's — cognition_panel.js (9.24 · laco vivo 3/3): a UI mostra a cognicao.
 * Consome o resultado real da missao (evento ants:task-done): a trilha cognitiva
 * TIPADA (cognitive_trace), a cadeia de fallback (de qual degrau saiu, se escalou
 * ao humano) e o modo de deliberacao quando presente. Nunca inventa: se o dado
 * nao veio, mostra estado vazio honesto. Aditivo; nao toca nos JS legados. */
(function () {
  "use strict";
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; });
  };

  // Resumo puro do resultado (facil de inspecionar/testar).
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

  function panel() {
    var el = document.getElementById("ants-cognition");
    if (el || !document.body) return el;
    el = document.createElement("div");
    el.id = "ants-cognition";
    el.style.cssText = "position:fixed;left:14px;bottom:14px;z-index:9998;width:290px;" +
      "background:var(--ant-bg-surface,#1e1810);color:var(--ant-text,#ece3d2);" +
      "border:1px solid var(--border,#3a2f1c);border-radius:10px;padding:10px 12px;" +
      "font:12px system-ui,sans-serif;box-shadow:0 6px 24px rgba(0,0,0,.4)";
    document.body.appendChild(el);
    return el;
  }

  function render(result) {
    var s = summarize(result);
    if (!s.steps && !s.reached) return;          // sem dado real → nao mostra nada
    var box = panel();
    if (!box) return;
    var kinds = Object.keys(s.counts).map(function (k) {
      return esc(k) + ":" + s.counts[k]; }).join("  ");
    var ladder = s.reached
      ? '<div>Fallback: <b>' + esc(s.reached) + '</b>' +
        (s.escalate ? ' <span style="color:var(--err,#c25a4e)">· precisa de humano</span>' : '') + '</div>'
      : "";
    var modeLine = s.mode ? '<div>Modo: <b>' + esc(s.mode) + '</b></div>' : "";
    box.innerHTML =
      '<div style="font-weight:600;margin-bottom:6px">Cognição da missão</div>' +
      ladder + modeLine +
      '<div>Trilha: <b>' + s.steps + '</b> passos</div>' +
      (kinds ? '<div style="color:var(--ant-text-secondary,#a89a80);margin-top:4px">' + kinds + '</div>' : "");
  }

  window.AntCognition = { summarize: summarize, render: render };

  document.addEventListener("ants:task-done", function (e) {
    var st = e.detail || {};
    try { render(st.result || {}); } catch (err) { /* nunca derruba a UI */ }
  });
})();
