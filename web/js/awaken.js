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

  // Backend não respondeu: erro com dignidade — estado adormecido honesto
  // com um botão "Tentar acordar" (o free tier hiberna e leva ~30-50s).
  function dormant(o, rotate) {
    clearInterval(rotate);
    var msg = o.querySelector(".aw-msg");
    var sub = o.querySelector(".aw-sub");
    if (msg) msg.textContent = "Colônia adormecida.";
    if (sub) sub.textContent = "O servidor pode estar hibernando (free tier acorda em ~30-50s).";
    if (!o.querySelector(".aw-retry")) {
      var btn = document.createElement("button");
      btn.className = "aw-retry";
      btn.textContent = "Tentar acordar";
      btn.style.cssText = "margin-top:16px;min-height:48px;padding:0 22px;border-radius:24px;" +
        "font-family:var(--mono,monospace);font-size:13px;cursor:pointer;border:1px solid var(--amber,#d4a017);" +
        "background:var(--amber,#d4a017);color:#1a1204";
      btn.onclick = function () { o.querySelector(".aw-retry").remove(); loop(o, restart(o)); };
      o.appendChild(btn);
    }
  }

  function restart(o) {
    var msgEl = o.querySelector(".aw-msg");
    var i = 0;
    return setInterval(function () { i = (i + 1) % MSGS.length; msgEl.textContent = MSGS[i]; }, 900);
  }

  function loop(o, rotate) {
    var msgEl = o.querySelector(".aw-msg");
    var deadline = Date.now() + 6000;
    (function poll() {
      fetch(api + "/health", { cache: "no-store" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) {
          if (d && d.status === "healthy") { msgEl.textContent = "Colônia desperta."; setTimeout(function () { done(o, rotate); }, 350); }
          else if (Date.now() < deadline) setTimeout(poll, 400);
          else dormant(o, rotate);
        })
        .catch(function () { if (Date.now() < deadline) setTimeout(poll, 500); else dormant(o, rotate); });
    })();
  }

  function start() {
    if (sessionStorage.getItem("ant-awoken")) {
      document.dispatchEvent(new CustomEvent("ants:awake"));
      return;
    }
    sessionStorage.setItem("ant-awoken", "1");
    var o = build();
    document.body.appendChild(o);
    loop(o, restart(o));
  }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", start);
  else start();
})();
