/* Ant's — context_engine.js: a interface se reorganiza pelo estado da colônia.
   Aditivo e puramente visual: não altera a lógica dos JS originais.
   Aplica um atributo data-colony-state no #app, que o design_system.css usa
   para mudar discretamente o tema (cores, glow, animações). */
(function () {
  "use strict";
  const STATES = {
    dormant:   { label: "Adormecida",  icon: "i-mem" },
    observing: { label: "Observando",  icon: "i-compass" },
    exploring: { label: "Explorando",  icon: "i-compass" },
    building:  { label: "Construindo", icon: "i-factory" },
    learning:  { label: "Aprendendo",  icon: "i-mem" },
    defending: { label: "Defendendo",  icon: "i-shield" },
    executing: { label: "Executando",  icon: "i-zap" },
    emergency: { label: "Emergência",  icon: "i-shield" },
  };
  let current = "dormant";
  const listeners = [];

  function ensureIndicator() {
    let el = document.getElementById("colony-state-indicator");
    if (!el) {
      el = document.createElement("span");
      el.id = "colony-state-indicator";
      el.className = "state-indicator";
      const conn = document.getElementById("conn");
      if (conn && conn.parentElement) conn.parentElement.insertBefore(el, conn);
    }
    return el;
  }

  function setContext(state) {
    if (!STATES[state]) return;
    current = state;
    const app = document.getElementById("app");
    if (app) app.setAttribute("data-colony-state", state);
    const ind = ensureIndicator();
    ind.textContent = STATES[state].label;
    // reflete no indicador do design (topbar)
    const si = document.getElementById("state-ind");
    if (si) si.textContent = STATES[state].label;
    // trilhas de feromônio no conteúdo só quando a colônia trabalha
    const content = document.querySelector(".content");
    if (content) {
      content.classList.add("bg-pheromone-trails");
      content.classList.toggle("colony-working",
        state !== "dormant" && state !== "observing");
    }
    listeners.forEach((cb) => { try { cb(state); } catch (e) {} });
  }

  function getCurrentContext() { return current; }
  function registerContextChange(cb) {
    if (typeof cb === "function") listeners.push(cb);
  }

  // Deriva o estado a partir do texto de um objetivo (heurística leve).
  function inferFromGoal(goal) {
    const g = (goal || "").toLowerCase();
    if (/cri(e|ar)|app|api|constr/.test(g)) return "building";
    if (/pesquis|busca|encontr|descob/.test(g)) return "exploring";
    if (/analis|process|document|dados/.test(g)) return "executing";
    if (/protej|segur|defend|amea/.test(g)) return "defending";
    if (/aprend|memó|consolid|sono/.test(g)) return "learning";
    return "observing";
  }

  window.AntContext = { setContext, getCurrentContext,
                        registerContextChange, inferFromGoal, STATES };
  document.addEventListener("DOMContentLoaded", () => {
    ensureIndicator();
    setContext("dormant");
    // liga-se ao envio de mensagens para refletir o estado automaticamente
    const send = document.getElementById("chat-send");
    const input = document.getElementById("chat-input");
    function react() {
      if (input && input.value.trim()) setContext(inferFromGoal(input.value));
      setTimeout(() => setContext("observing"), 6000);
    }
    if (send) send.addEventListener("click", react);
    if (input) input.addEventListener("keydown",
      (e) => { if (e.key === "Enter") react(); });
  });
})();
