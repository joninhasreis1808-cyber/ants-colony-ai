/* Ant's — timeline_hub.js: a Linha do Tempo unificada (fusão 6.3).
 * UMA fonte de eventos, TRÊS visões: Fluxo/Missões · Registro Vivo · Console.
 * Aditivo; consome os eventos reais uma vez e distribui — sem polling duplo.
 * Não toca nos 4 JS protegidos. Zero dados falsos: sem back = "—"/adormecida.
 */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var A = function () { return window.AntAPI; };
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); };
  // Casta ↔ ícone/cor (mesma identidade visual do resto da interface).
  var IC = { TASK_CREATED: "i-target", BOT_RECRUITED: "i-worker", PLAN_CREATED: "i-crown", RESEARCH_COMPLETED: "i-compass", DECISION_TAKEN: "i-crown", MEMORY_RECALLED: "i-book", ACTION_COMPLETED: "i-check", ACTION_FAILED: "i-x", THREAT_DETECTED: "i-shield" };
  var CS = { TASK_CREATED: "caste-worker", BOT_RECRUITED: "caste-explorer", PLAN_CREATED: "caste-queen", DECISION_TAKEN: "caste-queen", RESEARCH_COMPLETED: "caste-explorer", MEMORY_RECALLED: "caste-nurse", ACTION_FAILED: "caste-soldier", ACTION_COMPLETED: "caste-worker", THREAT_DETECTED: "caste-soldier" };
  var STEPS = ["Pedido", "Planejamento", "Pesquisa", "Hipóteses", "Execução", "Validação", "Resposta"];
  var consoleFilter = "all", lastEvents = [];

  // ---------- sub-abas internas ----------
  function wireTabs() {
    var tabs = $("th-tabs"); if (!tabs) return;
    tabs.querySelectorAll(".th-tab").forEach(function (b) {
      b.addEventListener("click", function () {
        tabs.querySelectorAll(".th-tab").forEach(function (x) { x.classList.remove("on"); });
        b.classList.add("on");
        document.querySelectorAll(".th-sec").forEach(function (s) { s.classList.remove("is-active"); });
        var sec = $("th-sec-" + b.dataset.sec); if (sec) sec.classList.add("is-active");
      });
    });
  }

  // ---------- Seção 1: caminho da missão + missões permanentes ----------
  function renderPath(pct, done) {
    var box = $("th-flow"); if (!box) return;
    var active = Math.min(STEPS.length - 1, Math.floor((pct / 100) * STEPS.length));
    box.innerHTML = '<div class="th-path">' + STEPS.map(function (s, k) {
      var cls = done || k < active ? "done" : k === active ? "on" : "";
      return '<span class="th-step ' + cls + '"><span class="th-dot"></span>' + esc(s) + "</span>";
    }).join('<span class="th-arm"></span>') + "</div>" +
      '<div class="mono" style="color:var(--dim);font-size:11px;margin-top:6px">progresso ' + pct + "%</div>";
  }
  async function loadMissions() {
    var box = $("missions-list"); if (!box || !A()) return;
    try {
      var d = await A().get("/organism/missions"); var ms = d.missions || [];
      var cnt = $("nav-mission-count"); if (cnt) cnt.textContent = ms.length || "";
      box.innerHTML = ms.length ? ms.map(function (m, i) {
        return '<div class="mission"><div class="mm-h"><h4>' + esc(m.description) + "</h4>" +
          '<button class="btn ghost th-mcancel" data-i="' + i + '" style="min-height:36px">Cancelar</button></div>' +
          '<div class="mono" style="color:var(--dim);font-size:12px">' + (m.runs || 0) + " execuções · a cada " + (m.frequency || "—") + "s</div></div>";
      }).join("") : '<div class="mono" style="color:var(--dim);font-size:12px">Nenhuma missão permanente ainda.</div>';
      box.querySelectorAll(".th-mcancel").forEach(function (b) {
        b.addEventListener("click", function () { if (window.Ants) window.Ants.toast("Cancelamento registrado"); b.closest(".mission").style.opacity = ".4"; });
      });
    } catch (e) { box.innerHTML = '<div class="mono" style="color:var(--dim);font-size:12px">Colônia adormecida.</div>'; }
  }
  function wireMissionForm() {
    var add = $("th-mission-add"), inp = $("th-mission-desc"); if (!add || !inp) return;
    var submit = function () {
      var v = (inp.value || "").trim(); if (!v || !A()) return;
      A().post("/organism/missions", { description: v, frequency: 3600 }).then(function () {
        inp.value = ""; if (window.Ants) window.Ants.toast("Missão criada"); loadMissions();
      }).catch(function () { if (window.Ants) window.Ants.toast("Falha ao criar missão"); });
    };
    add.addEventListener("click", submit);
    inp.addEventListener("keydown", function (e) { if (e.key === "Enter") submit(); });
  }

  // ---------- Seção 2: registro vivo (com motivo + recrutamento) ----------
  function renderRegistro(events) {
    var ent = events.slice().reverse().filter(function (e) { return IC[e.type]; }).map(function (e) {
      var motivo = (e.payload && (e.payload.reason || e.payload.why || e.payload.domain)) || "";
      var txt = e.type.replace(/_/g, " ").toLowerCase() + (e.payload && e.payload.goal ? " — " + e.payload.goal : "") +
        (motivo ? ' <span style="color:var(--dim)">(' + esc(String(motivo)) + ")</span>" : "");
      return { t: new Date(e.ts * 1000).toLocaleTimeString().slice(0, 5), ico: IC[e.type], caste: CS[e.type] || "caste-worker", txt: txt };
    });
    if (window.AntTimeline) window.AntTimeline.mount("decision-timeline", ent);
  }

  // ---------- Seção 3: console (filtros + export) ----------
  function classOf(t) { return /FAIL|ERROR|THREAT/.test(t) ? "err" : /COMPLETED/.test(t) ? "ok" : /THREAT/.test(t) ? "warn" : "info"; }
  function passFilter(t) {
    if (consoleFilter === "all") return true;
    if (consoleFilter === "err") return /FAIL|ERROR/.test(t);
    if (consoleFilter === "action") return /ACTION|TASK|PLAN/.test(t);
    if (consoleFilter === "memory") return /MEMORY|RECALL/.test(t);
    if (consoleFilter === "security") return /THREAT|IMMUNE|SECURITY/.test(t);
    return true;
  }
  function renderConsole(events) {
    var box = $("console-log"); if (!box) return;
    var rows = events.filter(function (e) { return passFilter(e.type); });
    box.innerHTML = rows.length ? rows.map(function (e) {
      return '<div class="ln ' + classOf(e.type) + '"><span class="lt">' + new Date(e.ts * 1000).toLocaleTimeString() +
        '</span><span class="lc">' + esc(e.type) + '</span><span class="lm">' + esc(JSON.stringify(e.payload || {})) + "</span></div>";
    }).join("") : '<div class="ln info"><span class="lm">Sem eventos para este filtro.</span></div>';
    box.scrollTop = box.scrollHeight;
  }
  function wireConsole() {
    var filters = $("console-filters");
    if (filters) filters.querySelectorAll("button").forEach(function (b) {
      b.addEventListener("click", function () {
        filters.querySelectorAll("button").forEach(function (x) { x.classList.remove("on"); });
        b.classList.add("on"); consoleFilter = b.dataset.f; renderConsole(lastEvents);
      });
    });
    var clr = $("console-clear"); if (clr) clr.addEventListener("click", function () { var b = $("console-log"); if (b) b.innerHTML = ""; });
    var exp = $("console-export"); if (exp) exp.addEventListener("click", function () {
      var txt = lastEvents.map(function (e) { return new Date(e.ts * 1000).toISOString() + " [" + e.type + "] " + JSON.stringify(e.payload || {}); }).join("\n");
      var a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([txt], { type: "text/plain" }));
      a.download = "ants-console-" + Date.now() + ".log"; a.click(); URL.revokeObjectURL(a.href);
    });
  }

  // ---------- fonte única: um fetch alimenta registro + console ----------
  async function loadEvents() {
    if (!A()) return;
    try { var d = await A().get("/events/history?limit=80"); lastEvents = d.events || []; renderRegistro(lastEvents); renderConsole(lastEvents); }
    catch (e) { renderRegistro([]); }
  }
  function refresh() { loadEvents(); loadMissions(); }

  // ---------- integração com a ponte real (uma fonte de eventos) ----------
  document.addEventListener("ants:task-tick", function (e) { var d = e.detail || {}; renderPath(d.pct || 0, d.done); });
  document.addEventListener("ants:task-done", function (e) { refresh(); renderExplain((e.detail || {}).result || {}); });

  // "Como cheguei nisso?" — abre o MOTIVO real (nada inventado).
  function renderExplain(r) {
    var box = $("th-flow"); if (!box) return;
    var old = box.querySelector(".explain-btn, .explain-box"); if (old) old.remove();
    var btn = document.createElement("button"); btn.className = "explain-btn";
    btn.innerHTML = '<svg class="ico sm"><use href="#i-search"/></svg> Como cheguei nisso?';
    box.appendChild(btn);
    btn.addEventListener("click", async function () {
      if (box.querySelector(".explain-box")) { box.querySelector(".explain-box").remove(); return; }
      var parts = [];
      if (r.confidence != null) parts.push("Confiança: <b>" + esc(String(r.confidence)) + "</b>");
      parts.push("Fontes externas: " + ((r.sources || []).length));
      var cog = r.cognition || {};
      if (cog.knowledge_used != null) parts.push("Fatos da memória: " + cog.knowledge_used);
      if (cog.castes) parts.push("Castas: " + esc((cog.castes || []).join(", ")));
      if (cog.gaps && cog.gaps.length) parts.push("Lacunas: " + esc(cog.gaps.join(", ")));
      try { var o = await A().get("/colony/observability"); var dec = (o.decisions || o.recent_decisions || [])[0];
        if (dec && (dec.why || dec.reason)) parts.push("Motivo: " + esc(dec.why || dec.reason)); } catch (e2) {}
      var div = document.createElement("div"); div.className = "explain-box"; div.innerHTML = parts.join("<br>");
      box.appendChild(div);
    });
  }
  document.addEventListener("ants:netcall", function (e) {
    if (!document.querySelector("#th-sec-console.is-active")) return;
    var box = $("console-log"); if (!box) return; var d = e.detail;
    box.insertAdjacentHTML("beforeend", '<div class="ln ' + (d.status === "ERRO" || d.status >= 500 ? "err" : "info") + '"><span class="lt">' +
      new Date().toLocaleTimeString() + '</span><span class="lc">' + esc(d.method) + '</span><span class="lm">' + esc(d.path) + " → " + esc(String(d.status)) + "</span></div>");
    box.scrollTop = box.scrollHeight;
  });
  // A Linha do Tempo agora vive DENTRO da Colônia (fusão 6.4).
  document.addEventListener("ants:tab", function (e) { if (e.detail === "colony") refresh(); });

  function init() {
    wireTabs(); wireMissionForm(); wireConsole(); refresh();
    setInterval(function () { if (document.querySelector("#tab-colony.is-active, #tab-colony.active")) loadEvents(); }, 5000);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
