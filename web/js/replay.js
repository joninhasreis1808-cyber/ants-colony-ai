/* Ant's — replay de tarefas (aditivo, só UI, sem emojis).
   Reproduz o histórico de eventos do EventBus em 10x, mostrando cada etapa. */
(function () {
  var LABELS = {
    TASK_CREATED: "Tarefa criada", BOT_RECRUITED: "Bots recrutados",
    PLAN_CREATED: "Plano criado", RESEARCH_COMPLETED: "Pesquisa concluída",
    DECISION_TAKEN: "Decisão tomada", MEMORY_RECALLED: "Memória recuperada",
    ACTION_COMPLETED: "Ação concluída", ACTION_FAILED: "Ação falhou",
  };

  function play(container, events, speed) {
    var el = typeof container === "string" ? document.getElementById(container) : container;
    if (!el) return;
    var list = (events || []).filter(function (e) { return LABELS[e.type]; });
    el.innerHTML = "";
    if (!list.length) { el.innerHTML = '<p class="muted">Nada para reproduzir.</p>'; return; }
    var i = 0;
    var step = Math.max(60, 600 / (speed || 10));
    (function tick() {
      if (i >= list.length) return;
      var e = list[i++];
      var row = document.createElement("div");
      row.className = "rp-row";
      row.textContent = (LABELS[e.type] || e.type) +
        (e.payload && e.payload.goal ? " — " + e.payload.goal : "");
      el.appendChild(row);
      el.scrollTop = el.scrollHeight;
      setTimeout(tick, step);
    })();
  }

  window.AntReplay = { play: play };
})();
