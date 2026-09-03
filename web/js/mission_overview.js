/* Ant's — mission_overview.js (fund. 06 · item 6, Nível 1 do §3): "uma
 * linha: o que foi pedido; uma barra: quanto falta" — sempre no topbar,
 * visível em QUALQUER aba, não só dentro do Fluxo da Colônia (que fica
 * escondido atrás da aba "Colônia"). Reaproveita os MESMOS eventos reais
 * que o Fluxo já usa (`ants:task-tick`/`ants:task-done`, de api_bridge.js) —
 * nenhum dado novo, só um segundo lugar honesto para mostrá-lo.
 *
 * Sem missão: o elemento fica `hidden` de verdade, não uma barra em 0%
 * decorativa. "Interface nunca inventa" vale aqui como em todo o resto.
 */
(function () {
  "use strict";

  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c];
    });
  };

  var goalCache = {};   // taskId -> goal (a WS não repete o goal a cada tick)
  var hideTimer = null;

  function fetchGoal(taskId) {
    if (!window.AntAPI || goalCache[taskId] !== undefined) return;
    goalCache[taskId] = null;   // evita pedidos duplicados enquanto resolve
    window.AntAPI.get("/hive/status/" + taskId).then(function (st) {
      goalCache[taskId] = (st && st.goal) || "";
      paint(taskId);
    }).catch(function () {});
  }

  var lastTaskId = null, lastPct = 0, lastDone = false;

  function paint(taskId) {
    var line = document.getElementById("mo-line");
    var goalEl = document.getElementById("mo-goal");
    var pctEl = document.getElementById("mo-pct");
    if (!line || !goalEl || !pctEl) return;
    var goal = goalCache[taskId];
    if (!goal) return;   // ainda não sabemos o objetivo — não mostra vazio
    clearTimeout(hideTimer);
    line.hidden = false;
    goalEl.innerHTML = esc(goal);
    pctEl.textContent = lastDone ? "concluído" : lastPct + "%";
  }

  document.addEventListener("ants:task-tick", function (e) {
    var d = e.detail || {};
    lastTaskId = d.taskId; lastPct = d.pct || 0; lastDone = !!d.done;
    var st = d.status || {};
    if (st.goal && goalCache[lastTaskId] === undefined) goalCache[lastTaskId] = st.goal;
    if (goalCache[lastTaskId] === undefined) fetchGoal(lastTaskId);
    paint(lastTaskId);
  });

  document.addEventListener("ants:task-done", function () {
    lastDone = true; lastPct = 100;
    paint(lastTaskId);
    // Fica visível um instante depois de concluir, depois volta ao vazio
    // honesto — nada de "concluído" pendurado pra sempre no topbar.
    clearTimeout(hideTimer);
    hideTimer = setTimeout(function () {
      var line = document.getElementById("mo-line");
      if (line) line.hidden = true;
    }, 4000);
  });
})();
