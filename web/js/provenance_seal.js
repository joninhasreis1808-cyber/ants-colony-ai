/* Ant's — provenance_seal.js (9.4 · T3): a ORIGEM de cada resposta, visível.
 * Três comportamentos tinham aparência idêntica (cache, memória interna, web).
 * Aqui cada resposta ganha um selo honesto com a fonte real
 * (result.provenance.source) e, quando veio da memória/base, o botão
 * "buscar de novo" (força o pipeline ignorando o cache — via T3 no backend).
 * Aditivo; não toca no chat.js legado. Sem emojis (SVG). */
(function () {
  "use strict";
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>]/g,
    function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); };
  var LABEL = {
    computation: { t: "cálculo exato", ico: "i-target" },
    web_search: { t: "busca na web", ico: "i-globe" },
    memory: { t: "resposta da memória · repetida", ico: "i-brain", again: true },
    knowledge_base: { t: "conhecimento interno da colônia", ico: "i-book", web: true },
    seed_knowledge: { t: "conhecimento interno da colônia", ico: "i-book", web: true },
    reasoning: { t: "raciocínio próprio", ico: "i-brain" },
    analogy: { t: "analogia com um caso anterior", ico: "i-brain" },
    none: { t: "não sei — sem evidência suficiente", ico: "i-x" },
  };
  var lastTask = null;

  document.addEventListener("ants:task-done", function (e) {
    var st = e.detail || {}, r = st.result || {};
    var prov = r.provenance || {};
    var src = prov.source || (r.sources && r.sources.length ? "web_search" : "none");
    if (prov.cached && src === "memory") src = "memory";
    var meta = LABEL[src] || { t: src, ico: "i-ant" };
    var tid = st.id || st.task_id;
    if (tid && tid === lastTask) return;          // um selo por missão
    lastTask = tid;
    var box = document.getElementById("messages"); if (!box) return;
    var bots = box.querySelectorAll(".msg.bot");
    var msg = bots[bots.length - 1]; if (!msg) return;
    // Selo por missão: NÃO é filho da mensagem (o chat.js legado reescreve o
    // textContent dela e apagaria o selo) — vai como IRMÃO, logo após.
    if (msg.nextSibling && msg.nextSibling.classList
        && msg.nextSibling.classList.contains("prov-seal")) return;

    var nsrc = (r.sources || []).length || (prov.urls || []).length;
    var cachedTag = prov.cached ? " · da memória (repetida)" : "";
    var label = meta.t + cachedTag
      + (src === "web_search" && nsrc ? " · " + nsrc + " fonte(s)" : "");
    var conf = (r.confidence != null) ? " · confiança " + r.confidence : "";
    var again = (meta.again || meta.web || prov.cached);

    var seal = document.createElement("div");
    seal.className = "prov-seal";
    seal.innerHTML =
      '<span class="ps-chip"><svg class="ico sm"><use href="#' + meta.ico + '"/></svg>'
      + esc(label) + esc(conf) + "</span>"
      + (again ? '<button class="ps-again" type="button">'
          + (meta.web ? "procurar na web" : "buscar de novo") + "</button>" : "");
    msg.parentNode.insertBefore(seal, msg.nextSibling);   // irmão, não filho

    var btn = seal.querySelector(".ps-again");
    if (btn) btn.onclick = function () {
      var goal = window.__antLastQuestion; if (!goal) return;
      var input = document.getElementById("chat-input");
      var send = document.getElementById("chat-send");
      if (!input || !send) return;
      window.__antFresh = true;                   // api_bridge injeta fresh:true
      input.value = goal;
      send.click();
    };
  });
})();
