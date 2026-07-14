/* Ant's — tour de boas-vindas (aditivo, só UI, primeira visita).
   3 passos, dispensável. Marca localStorage para não repetir. Sem emojis. */
(function () {
  var STEPS = [
    { h: "A Colônia", p: "Esta é a Colônia — aqui você conversa com a IA e dá tarefas ao superorganismo." },
    { h: "O Centro Cognitivo", p: "Veja o cérebro funcionando: camadas, hipóteses e decisões passo a passo." },
    { h: "Pronto!", p: "É só começar a usar. A colônia aprende com o seu feedback a cada decisão." },
  ];

  function render(i, overlay) {
    var dots = STEPS.map(function (_, k) {
      return '<i class="' + (k === i ? "on" : "") + '"></i>';
    }).join("");
    var last = i === STEPS.length - 1;
    overlay.innerHTML =
      '<div class="card" role="dialog" aria-modal="true" aria-label="Tour do Ant\'s">' +
      "<h3>" + STEPS[i].h + "</h3><p>" + STEPS[i].p + "</p>" +
      '<div class="dots">' + dots + "</div>" +
      '<div class="row"><button class="skip">Pular</button>' +
      '<button class="next">' + (last ? "Começar" : "Próximo") + "</button></div></div>";
    overlay.querySelector(".skip").onclick = finish.bind(null, overlay);
    overlay.querySelector(".next").onclick = function () {
      if (last) finish(overlay); else render(i + 1, overlay);
    };
    overlay.querySelector(".next").focus();
  }

  function finish(overlay) {
    localStorage.setItem("ants-onboarded", "1");
    if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
  }

  function open() {
    if (localStorage.getItem("ants-onboarded")) return;
    var overlay = document.createElement("div");
    overlay.id = "ant-tour";
    document.body.appendChild(overlay);
    render(0, overlay);
    overlay.addEventListener("keydown", function (e) {
      if (e.key === "Escape") finish(overlay);
    });
  }

  // espera a colônia "despertar" para não competir com o splash
  document.addEventListener("ants:awake", function () { setTimeout(open, 400); });
})();
