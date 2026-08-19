/* Ant's — rodapé de saúde (aditivo, só UI).
   Mostra "Todos os sistemas operacionais" ou "N/M módulos ativos",
   ou "Colônia adormecida" se o backend não responder. Sem emojis. */
(function () {
  var api = location.origin;

  function el() {
    var f = document.getElementById("ant-health-footer");
    if (f) return f;
    f = document.createElement("div");
    f.id = "ant-health-footer";
    f.setAttribute("role", "status");
    f.setAttribute("aria-live", "polite");
    f.innerHTML = '<span class="dot"></span><span class="txt">Conectando à colônia...</span>';
    document.body.appendChild(f);
    return f;
  }

  function set(state, text) {
    var f = el();
    f.classList.remove("warn", "down");
    if (state) f.classList.add(state);
    f.querySelector(".txt").textContent = text;
  }

  // Fonte ÚNICA (9.4 · T6): não faz fetch próprio; ouve "ants:health" emitido
  // pelo app.js (um /health por ciclo) e só renderiza. Zero requisição extra.
  function render(d) {
    if (!d || !d.modules) { set("down", "Colônia adormecida"); return; }
    var mods = d.modules;
    var total = Object.keys(mods).length;
    var on = Object.keys(mods).filter(function (k) { return mods[k]; }).length;
    if (on === total && d.status === "healthy")
      set("", "Todos os sistemas operacionais");
    else
      set("warn", on + "/" + total + " módulos ativos");
  }

  document.addEventListener("ants:health", function (e) { render(e.detail); });
  // render inicial se o app já tem a saúde em mãos.
  function start() { if (window.Ant && window.Ant._health) render(window.Ant._health); }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", start);
  else start();
})();
