/* Ant's — tela de "colônia despertando" (aditivo, só UI).
   Aparece no primeiro carregamento e some quando /health responde.
   Sem emojis; usa o ícone do sprite. Degrada com timeout. */
(function () {
  var MSGS = [
    "Acordando a Rainha...",
    "Despertando as Operárias...",
    "Ativando os Soldados...",
    "Sincronizando a memória...",
    "Lendo os feromônios...",
  ];
  var api = location.origin;

  function build() {
    var o = document.createElement("div");
    o.id = "ant-awaken";
    o.setAttribute("role", "status");
    o.setAttribute("aria-live", "polite");
    o.innerHTML =
      '<div class="aw-ant"><svg viewBox="0 0 24 24" aria-hidden="true">' +
      '<use href="#i-ant"/></svg></div>' +
      '<div class="aw-msg">' + MSGS[0] + "</div>" +
      '<div class="aw-sub">Superorganismo Digital</div>';
    return o;
  }

  function done(o, rotate) {
    clearInterval(rotate);
    o.classList.add("hide");
    document.dispatchEvent(new CustomEvent("ants:awake"));
    setTimeout(function () { if (o.parentNode) o.parentNode.removeChild(o); }, 600);
  }

  function start() {
    if (sessionStorage.getItem("ant-awoken")) {
      document.dispatchEvent(new CustomEvent("ants:awake"));
      return;
    }
    sessionStorage.setItem("ant-awoken", "1");
    var o = build();
    document.body.appendChild(o);
    var msgEl = o.querySelector(".aw-msg");
    var i = 0;
    var rotate = setInterval(function () {
      i = (i + 1) % MSGS.length;
      msgEl.textContent = MSGS[i];
    }, 900);

    var deadline = Date.now() + 12000;
    (function poll() {
      fetch(api + "/health", { cache: "no-store" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) {
          if (d && d.status === "healthy") { msgEl.textContent = "Colônia desperta."; setTimeout(function () { done(o, rotate); }, 350); }
          else if (Date.now() < deadline) setTimeout(poll, 400);
          else done(o, rotate);
        })
        .catch(function () { if (Date.now() < deadline) setTimeout(poll, 500); else done(o, rotate); });
    })();
  }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", start);
  else start();
})();
