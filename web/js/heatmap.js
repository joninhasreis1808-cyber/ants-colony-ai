/* Ant's — heatmap de bots (aditivo, só UI, sem emojis).
   Conta a atividade por bot a partir dos eventos BOT_RECRUITED e pinta
   células (verde=pouco, amarelo=médio, vermelho=muito). */
(function () {
  function tally(events) {
    var counts = {};
    (events || []).forEach(function (e) {
      if (e.type !== "BOT_RECRUITED") return;
      (e.payload && e.payload.bots || []).forEach(function (b) {
        counts[b] = (counts[b] || 0) + 1;
      });
    });
    return counts;
  }

  function color(v, max) {
    if (max <= 0) return "#3d7a3d";
    var r = v / max;
    if (r < 0.34) return "#3d7a3d";
    if (r < 0.67) return "#d4a017";
    return "#8b0000";
  }

  function render(container, events) {
    var el = typeof container === "string" ? document.getElementById(container) : container;
    if (!el) return;
    var counts = tally(events);
    var names = Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; });
    var max = names.reduce(function (m, n) { return Math.max(m, counts[n]); }, 0);
    if (!names.length) { el.innerHTML = '<p class="muted">Sem atividade de bots ainda.</p>'; return; }
    el.innerHTML = names.map(function (n) {
      return '<div class="hm-cell" style="background:' + color(counts[n], max) + '">' +
        '<span class="hm-name">' + n + "</span><span class=\"hm-n\">" + counts[n] + "</span></div>";
    }).join("");
  }

  window.AntHeatmap = { render: render, tally: tally };
})();
