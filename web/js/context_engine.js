/* Ant's — context_engine.js (fund. 06 · item 6 do Repertório da Colmeia):
 * o rótulo "estado da colônia" do topbar (#state-ind), agora REAL.
 *
 * O que havia antes: `inferFromGoal()` adivinhava o estado por PALAVRAS-CHAVE
 * no texto que o usuário digitou ("cri(e|ar)|app|api" → "Construindo", etc.)
 * e um `setTimeout` fixo de 6s devolvia "Observando" — sem relação nenhuma
 * com a colônia ter terminado de verdade. Três scripts diferentes (este,
 * ants_bridge.js, live_panels.js) escreviam no MESMO elemento em corrida,
 * o que ganhava por último vencia. `/colony/state` (backend real, ligado ao
 * barramento de eventos no PR #103) já existia e era consultado só quando o
 * usuário abria a aba "Recursos" — o resto do tempo, o rótulo visível era
 * pura adivinhação.
 *
 * Agora só ESTE módulo escreve em #state-ind/data-colony-state, e sempre a
 * partir de `/colony/state`. Três estados reais, sem embelezar: a colônia
 * não sabe dizer SE está "explorando" ou "construindo" — só se está
 * adormecida, ativa ou intensiva. Rotular mais fino que isso seria inventar.
 */
(function () {
  "use strict";

  var STATES = {
    dormant:   { label: "Adormecida" },
    active:    { label: "Ativa" },
    intensive: { label: "Intensiva" },
  };

  var current = null;
  var listeners = [];
  var lastEventAt = 0;

  function paint(state) {
    var meta = STATES[state] || STATES.dormant;
    current = state;
    var app = document.getElementById("app");
    if (app) app.setAttribute("data-colony-state", state);
    var ind = document.getElementById("state-ind");
    if (ind) ind.textContent = meta.label;
    listeners.forEach(function (cb) { try { cb(state); } catch (e) {} });
  }

  /* O pulso do ponto (`.is-live`) é sinal, não enfeite (regra da FASE D,
   * reafirmada no §3 do item 6): só anima nos ~4s depois de um evento REAL
   * do barramento (ants:task-tick), nunca continuamente. */
  function markLive() {
    lastEventAt = Date.now();
    var ind = document.getElementById("state-ind");
    if (ind) ind.classList.add("is-live");
  }
  setInterval(function () {
    if (lastEventAt && Date.now() - lastEventAt > 4000) {
      var ind = document.getElementById("state-ind");
      if (ind) ind.classList.remove("is-live");
      lastEventAt = 0;
    }
  }, 1000);

  function refresh() {
    if (!window.AntAPI) return;
    window.AntAPI.get("/colony/state").then(function (d) {
      if (d && d.state) paint(d.state);
    }).catch(function () { /* rede fora: mantém o último estado conhecido */ });
  }

  function getCurrentContext() { return current; }
  function registerContextChange(cb) {
    if (typeof cb === "function") listeners.push(cb);
  }

  window.AntContext = { getCurrentContext, registerContextChange, refresh, STATES };

  document.addEventListener("DOMContentLoaded", function () {
    refresh();
    setInterval(refresh, 8000);
  });
  document.addEventListener("ants:task-tick", function () { markLive(); });
  document.addEventListener("ants:task-done", function () {
    markLive();
    setTimeout(refresh, 300);   // dá tempo do backend registrar o desfecho
  });
})();
