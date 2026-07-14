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

  function tick() {
    fetch(api + "/health", { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d || !d.modules) { set("down", "Colônia adormecida"); return; }
        var mods = d.modules;
        var total = Object.keys(mods).length;
        var on = Object.keys(mods).filter(function (k) { return mods[k]; }).length;
        if (on === total && d.status === "healthy")
          set("", "Todos os sistemas operacionais");
        else
          set("warn", on + "/" + total + " módulos ativos");
      })
      .catch(function () { set("down", "Colônia adormecida"); });
  }

  function start() { tick(); setInterval(tick, 15000); }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", start);
  else start();
})();
