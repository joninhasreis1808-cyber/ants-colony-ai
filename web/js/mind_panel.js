/* Ant's — mind_panel.js (9.9 · FASE F): a "Mente da Colônia" visível.
 * Expõe, ao vivo e honestamente, a inteligência REAL do backend (FASES B–E): as
 * rotas que a Cartógrafa conhece, as ferramentas gated (com o risco de cada uma)
 * e as capacidades ativas (decisão coletiva, atenção emergente, divisão de
 * trabalho, laço autônomo) + o placar de aprendizado.
 * Fonte ÚNICA: o evento "ants:health" (9.4 · T6) — não faz fetch próprio.
 * Aditivo; NÃO toca nos 4 JS legados (chat/bots/memory/factory). Sem emojis. */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>]/g,
    function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); };
  var RISK = { low: "baixo", medium: "médio", high: "alto" };

  function injectStyle() {
    if ($("mind-panel-style")) return;
    var s = document.createElement("style");
    s.id = "mind-panel-style";
    s.textContent =
      "#mind-panel{border:1px solid var(--line,#2a2a2a);border-radius:12px;"
      + "padding:12px 14px;background:var(--card,rgba(255,255,255,.03))}"
      + "#mind-panel .mind-head{font-weight:700;margin-bottom:8px;color:var(--gold,#d4a017)}"
      + "#mind-panel .mind-row{margin:6px 0;font-size:13px;line-height:1.9}"
      + "#mind-panel .mind-row b{color:var(--dim,#9aa);margin-right:6px;"
      + "text-transform:uppercase;font-size:11px;letter-spacing:.04em}"
      + "#mind-panel .mind-route,#mind-panel .mind-cap,#mind-panel .mind-tool{"
      + "display:inline-block;padding:2px 8px;margin:2px 3px;border-radius:999px;"
      + "border:1px solid var(--line,#2a2a2a);font-size:12px}"
      + "#mind-panel .mind-cap{background:rgba(212,160,23,.12)}"
      + "#mind-panel .mind-tool.on{border-color:#2e7d32}"
      + "#mind-panel .mind-tool.off{opacity:.55;text-decoration:line-through}"
      + "#mind-panel .mind-learn{color:var(--dim,#9aa);font-size:12px}";
    document.head.appendChild(s);
  }

  function render(h) {
    var el = $("mind-panel"); if (!el) return;
    injectStyle();
    var intel = h && h.intelligence;
    if (!intel || !intel.hierarchical_planner) {
      el.innerHTML = '<div class="mind-head">Mente da Colônia</div>'
        + '<div class="mind-learn">aguardando o backend…</div>';
      return;
    }
    var caps = [
      ["planejador hierárquico", intel.hierarchical_planner],
      ["contradição", intel.contradiction_engine],
      ["desvio de objetivo", intel.goal_drift_guard],
      ["decisão coletiva", intel.collective_decision],
      ["atenção emergente", intel.attention_field],
      ["divisão de trabalho", intel.adaptive_labor],
      ["laço autônomo", intel.autonomous_loop],
    ].filter(function (c) { return c[1]; }).map(function (c) {
      return '<span class="mind-cap">' + esc(c[0]) + "</span>";
    }).join("");
    var routes = (intel.cartographer || []).map(function (r) {
      return '<span class="mind-route">' + esc(r) + "</span>";
    }).join("");
    var tools = (intel.tools || []).map(function (t) {
      return '<span class="mind-tool ' + (t.available ? "on" : "off")
        + '" title="' + (t.available ? "disponível agora" : "sem permissão concedida")
        + '">' + esc(t.name) + " · " + esc(RISK[t.risk] || t.risk) + "</span>";
    }).join("");
    var learn = intel.learning || {};
    el.innerHTML =
      '<div class="mind-head">Mente da Colônia</div>'
      + '<div class="mind-row"><b>rotas</b>' + routes + "</div>"
      + '<div class="mind-row"><b>capacidades</b>' + caps + "</div>"
      + '<div class="mind-row"><b>ferramentas</b>' + tools + "</div>"
      + '<div class="mind-row mind-learn">aprendizado: ' + (learn.successes || 0)
      + " acerto(s) · " + (learn.errors || 0) + " erro(s) · missão em "
      + "<code>/mission</code> · autônomo em <code>/mission/auto</code></div>";
  }

  document.addEventListener("ants:health", function (e) { render(e.detail); });
  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", function () { render(null); });
  else render(null);
})();
