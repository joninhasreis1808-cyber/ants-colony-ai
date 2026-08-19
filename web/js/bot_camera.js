/* Ant's — bot_camera.js (9.4 · T2): a Câmera ao Vivo da missão.
 * Mostra UM bot por vez, com DADO REAL: casta, papel, fase, ação e log.
 * Fonte única: o CustomEvent "ants:task-tick" que o api_bridge já emite
 * (detail.status.events = a lista real do backend). Nenhuma conexão nova.
 * Buffer: libera os eventos REAIS um a um (~380ms), acelerando se a fila
 * cresce — só muda QUANDO cada evento aparece, nunca O QUÊ (Regra 6).
 * Sem emojis (SVG). Missão de cache (sem bots) declara honestamente. */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>]/g,
    function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); };
  var STEP = 380;
  var META = {
    navigator: { caste: "Exploradoras", role: "procura fontes na web", icon: "i-compass" },
    extractor: { caste: "Operárias", role: "extrai o conteúdo", icon: "i-worker" },
    interpreter: { caste: "Operárias", role: "interpreta o material", icon: "i-brain" },
    decider: { caste: "Rainha", role: "decide a resposta", icon: "i-crown" },
    learner: { caste: "Cuidadoras", role: "guarda o aprendizado", icon: "i-leaf" },
  };
  var released = [], queue = [], seen = {}, timer = null, pinned = null,
      done = false, task = null;

  function reset() {
    released = []; queue = []; seen = {}; pinned = null; done = false;
    if (timer) { clearTimeout(timer); timer = null; }
  }

  document.addEventListener("ants:task-tick", function (e) {
    var d = e.detail || {}, st = d.status || {}, evs = st.events || [];
    if (d.taskId && d.taskId !== task) { reset(); task = d.taskId; }
    evs.forEach(function (ev) {
      var id = ev.id || (ev.bot + "|" + ev.phase + "|" + ev.ts);
      if (!seen[id]) { seen[id] = 1; queue.push(ev); }
    });
    done = !!d.done;
    if (!timer) pump();
    else render();
  });

  function pump() {
    if (!queue.length) { timer = null; render(); return; }
    var n = queue.length > 14 ? 3 : (queue.length > 7 ? 2 : 1);
    while (n-- > 0 && queue.length) released.push(queue.shift());
    render();
    timer = setTimeout(pump, STEP);
  }

  function bots() {
    var map = {}, order = [];
    released.forEach(function (ev) {
      if (ev.bot === "hive") return;
      if (!map[ev.bot]) { map[ev.bot] = { name: ev.bot, phases: {}, log: [],
        data: null, failed: false, done: false }; order.push(ev.bot); }
      var b = map[ev.bot];
      b.phases[ev.phase] = 1; b.log.push(ev);
      if (ev.data && Object.keys(ev.data).length) b.data = ev.data;
      if (ev.phase === "act") b.done = true;
      if (/reprovado|n[ãa]o teve sucesso/i.test(ev.message || "")) b.failed = true;
    });
    return order.map(function (k) { return map[k]; });
  }

  function action(b) {
    var d = b.data || {};
    if (d.attempts) return "provedores: " + d.attempts.join(", ");
    if (d.query) return 'busca: "' + d.query + '"';
    if (d.sources) return d.sources.length + " fonte(s) recebida(s)";
    if (d.extracted) return "extraiu " + (d.extracted.chunks || 0) + " trecho(s)";
    return (b.log.length ? b.log[b.log.length - 1].message : "trabalhando…");
  }

  function focusOf(bs) {
    if (pinned) { var p = bs.filter(function (b) { return b.name === pinned; })[0]; if (p) return p; }
    var active = bs.filter(function (b) { return !b.done; })[0];
    return active || bs[bs.length - 1];
  }

  function mode() {
    if (!done) return { t: "ao vivo", live: true };
    if (queue.length) return { t: "reproduzindo · " + queue.length + " na fila", live: true };
    return { t: "trajeto completo", live: false };
  }

  function render() {
    var el = $("bot-camera"); if (!el) return;
    var bs = bots();
    if (!bs.length) {
      el.innerHTML = done
        ? '<div class="cam-empty">Resposta recuperada da memória da colônia. '
          + 'Nenhum bot foi recrutado nesta missão — por isso não há trajeto para exibir.</div>'
        : '<div class="cam-empty">Envie um objetivo no Chat — a câmera acompanha a colônia ao vivo.</div>';
      return;
    }
    var f = focusOf(bs), m = mode(), meta = META[f.name] || { caste: "Colônia", role: "—", icon: "i-ant" };
    var phases = ["plan", "do", "check", "act"].map(function (p) {
      return '<span class="cam-ph ' + (f.phases[p] ? "on" : "") + '">' + p + "</span>";
    }).join("");
    var log = f.log.slice(-6).map(function (ev) {
      return '<div class="cam-ln"><span>' + esc(ev.phase) + "</span>" + esc(ev.message) + "</div>";
    }).join("");
    var roster = bs.map(function (b) {
      var cls = b.failed ? "fail" : (b.done ? "done" : "act");
      return '<button class="cam-chip ' + cls + (b.name === f.name ? " sel" : "")
        + '" data-bot="' + esc(b.name) + '"><span class="cam-dot"></span>' + esc(b.name) + "</button>";
    }).join("");
    el.innerHTML =
      '<div class="cam-head"><span class="cam-badge ' + (m.live ? "live" : "") + '">'
      + '<span class="cam-rec"></span>' + esc(m.t) + "</span>"
      + (pinned ? '<button class="cam-follow" id="cam-follow">Seguir colônia</button>' : "")
      + "</div>"
      + '<div class="cam-stage"><div class="cam-bot">'
      + '<svg class="ico"><use href="#' + meta.icon + '"/></svg>'
      + '<div><div class="cam-name">' + esc(f.name) + '</div>'
      + '<div class="cam-sub">' + esc(meta.caste) + " · " + esc(meta.role) + "</div></div>"
      + '<span class="cam-state ' + (f.failed ? "fail" : (f.done ? "done" : "act")) + '">'
      + (f.failed ? "reprovado" : (f.done ? "concluído" : "ativo")) + "</span></div>"
      + '<div class="cam-phases">' + phases + "</div>"
      + '<div class="cam-action">' + esc(action(f)) + "</div>"
      + '<div class="cam-log">' + log + "</div></div>"
      + '<div class="cam-roster">' + roster + "</div>";
    var fol = $("cam-follow"); if (fol) fol.onclick = function () { pinned = null; render(); };
    [].slice.call(el.querySelectorAll(".cam-chip")).forEach(function (c) {
      c.onclick = function () { pinned = c.getAttribute("data-bot"); render(); };
    });
  }

  document.addEventListener("DOMContentLoaded", render);
  render();
})();
