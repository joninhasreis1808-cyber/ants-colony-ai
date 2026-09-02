/* Ant's — epistemic_card.js (C1 · FASE C): o rotulo epistemico na tela.
 *
 * A FASE B ensinou a colonia a dizer que TIPO de conhecimento cada resposta e:
 * manchete, origem, verificacao cruzada, calibracao, recencia, uso de cortex
 * externo e os limites do que ela NAO checou. Tudo isso ja vinha no resultado
 * (result.epistemic) e nenhum arquivo do front lia. A tela mostrava um numero
 * de confianca e pronto.
 *
 * Aqui esse rotulo aparece — inteiro, sem interpretacao e sem enfeite.
 *
 * Regras respeitadas:
 *  - NAO toca nos 4 JS legados (MD5) nem em nenhum ID legado.
 *  - Vai como IRMAO da mensagem, nunca como filho: o chat.js legado reescreve o
 *    textContent e apagaria qualquer coisa colocada dentro (licao ja registrada
 *    no provenance_seal.js).
 *  - Sem emoji pictografico. Sem framework. Sem build.
 *  - Sem `epistemic` no resultado, NAO desenha nada. A interface nunca inventa.
 */
(function () {
  "use strict";

  var KEY = "ants:epi-collapsed";
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  };

  /* As seis manchetes do B4. A cor carrega o sentido; o texto carrega o fato.
   *
   * `sev` e o orcamento de MOVIMENTO (FASE D). A regra: o movimento e gasto
   * onde a colonia esta MENOS segura. Uma resposta contestada ou sem base
   * chega com enfase; uma verificada chega quieta. Movimento aqui e sinal, nao
   * enfeite — e nunca e o UNICO canal: a palavra e a cor ja dizem tudo, e com
   * `prefers-reduced-motion` o cartao fica estatico sem perder informacao. */
  var HEAD = {
    verificado:    { rot: "verificado",    cls: "epi-ok",  sev: "baixa" },
    fundamentado:  { rot: "fundamentado",  cls: "epi-ok",  sev: "baixa" },
    recordado:     { rot: "recordado",     cls: "epi-mid", sev: "baixa" },
    inferido:      { rot: "inferido",      cls: "epi-mid", sev: "media" },
    contestado:    { rot: "contestado",    cls: "epi-bad", sev: "alta" },
    sem_base:      { rot: "sem base",      cls: "epi-bad", sev: "alta" }
  };

  var EIXOS = [
    ["origin",       "origem"],
    ["verification", "verificacao"],
    ["calibration",  "calibracao"],
    ["recency",      "recencia"],
    ["cortex",       "cortex externo"]
  ];

  function collapsed() {
    try { return localStorage.getItem(KEY) === "1"; } catch (e) { return false; }
  }
  function setCollapsed(v) {
    try { localStorage.setItem(KEY, v ? "1" : "0"); } catch (e) { /* sem storage */ }
  }

  function render(epi) {
    var meta = HEAD[epi.headline] || { rot: epi.headline, cls: "epi-mid", sev: "media" };
    var linhas = EIXOS.map(function (par) {
      var v = epi[par[0]];
      if (!v) return "";
      return '<div class="epi-row"><span class="epi-k">' + esc(par[1])
        + '</span><span class="epi-v">' + esc(v) + "</span></div>";
    }).join("");

    var limites = (epi.limits || []).map(function (l) {
      return '<li class="epi-lim">' + esc(l) + "</li>";
    }).join("");
    var blocoLimites = limites
      ? '<div class="epi-row epi-row-lim"><span class="epi-k">nao checado</span>'
        + '<ul class="epi-lims">' + limites + "</ul></div>"
      : "";

    var conf = (epi.confidence == null) ? "sem confianca declarada"
      : "confianca " + esc(epi.confidence);

    var card = document.createElement("div");
    card.className = "epi-card" + (collapsed() ? " is-collapsed" : "");
    card.setAttribute("data-sev", meta.sev || "media");
    card.innerHTML =
      '<button class="epi-head" type="button" aria-expanded="'
        + (collapsed() ? "false" : "true") + '">'
      + '<span class="epi-badge ' + meta.cls + '">' + esc(meta.rot) + "</span>"
      + '<span class="epi-conf">' + conf + "</span>"
      + '<span class="epi-toggle" aria-hidden="true"></span>'
      + "</button>"
      + '<div class="epi-body">'
      + (epi.explanation
          ? '<p class="epi-why">' + esc(epi.explanation) + "</p>" : "")
      + linhas + blocoLimites
      + "</div>";

    card.querySelector(".epi-head").addEventListener("click", function () {
      var fechado = card.classList.toggle("is-collapsed");
      this.setAttribute("aria-expanded", fechado ? "false" : "true");
      setCollapsed(fechado);
    });
    return card;
  }

  var ultimaTarefa = null;

  document.addEventListener("ants:task-done", function (e) {
    var st = e.detail || {};
    var epi = (st.result || {}).epistemic;
    if (!epi || !epi.headline) return;      // sem rotulo, nada e desenhado

    var tid = st.id || st.task_id;
    if (tid && tid === ultimaTarefa) return;   // um cartao por missao
    ultimaTarefa = tid;

    var box = document.getElementById("messages");
    if (!box) return;
    var bots = box.querySelectorAll(".msg.bot");
    var msg = bots[bots.length - 1];
    if (!msg) return;

    /* Depois do selo de proveniencia, quando ele existir — os dois sao irmaos
     * da mensagem e a ordem de leitura fica: resposta, origem, avaliacao. */
    var ancora = msg;
    var prox = msg.nextSibling;
    if (prox && prox.classList && prox.classList.contains("prov-seal")) {
      ancora = prox;
    }
    if (ancora.nextSibling && ancora.nextSibling.classList
        && ancora.nextSibling.classList.contains("epi-card")) return;

    ancora.parentNode.insertBefore(render(epi), ancora.nextSibling);
    box.scrollTop = box.scrollHeight;
  });
})();
