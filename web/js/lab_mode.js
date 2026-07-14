/* Ant's — Modo Laboratório (aditivo, só UI, sem emojis).
   Painel flutuante para devs: feed de eventos, heatmap de bots e replay.
   Ativado por ?lab=true na URL ou window.AntLab.toggle(). */
(function () {
  var api = location.origin;
  var open = false;

  function panel() {
    var p = document.getElementById("ant-lab");
    if (p) return p;
    p = document.createElement("div");
    p.id = "ant-lab";
    p.innerHTML =
      '<header><strong>Modo Laboratório</strong>' +
      '<button id="lab-close" aria-label="Fechar">&times;</button></header>' +
      '<div class="lab-sec"><h4>Heatmap de bots (atividade)</h4><div id="lab-heatmap"></div></div>' +
      '<div class="lab-sec"><h4>Replay da colônia</h4>' +
      '<button id="lab-replay">Reproduzir 10x</button><div id="lab-replay-out"></div></div>' +
      '<div class="lab-sec"><h4>Eventos recentes</h4><div id="lab-feed"></div></div>';
    document.body.appendChild(p);
    p.querySelector("#lab-close").onclick = function () { toggle(false); };
    p.querySelector("#lab-replay").onclick = function () {
      fetchEvents(function (ev) { window.AntReplay && AntReplay.play("lab-replay-out", ev, 10); });
    };
    return p;
  }

  function fetchEvents(cb) {
    fetch(api + "/events/history?limit=200", { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : { events: [] }; })
      .then(function (d) { cb(d.events || []); })
      .catch(function () { cb([]); });
  }

  function refresh() {
    if (!open) return;
    fetchEvents(function (ev) {
      if (window.AntHeatmap) AntHeatmap.render("lab-heatmap", ev);
      var feed = document.getElementById("lab-feed");
      if (feed) feed.innerHTML = ev.slice(-40).reverse().map(function (e) {
        return '<div class="lab-ev"><span>' + e.type + "</span></div>";
      }).join("");
    });
  }

  function toggle(force) {
    open = force === undefined ? !open : force;
    panel().classList.toggle("show", open);
    if (open) refresh();
  }

  window.AntLab = { toggle: toggle };
  document.addEventListener("DOMContentLoaded", function () {
    if (new URLSearchParams(location.search).get("lab") === "true") toggle(true);
    setInterval(refresh, 4000);
  });
})();
