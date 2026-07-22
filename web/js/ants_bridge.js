/* Ant's — ants_bridge.js: a ponte REAL entre a IA e a interface.
 *
 * Aditivo e não-destrutivo: NÃO toca em chat.js/bots.js/memory.js/factory.js
 * (contrato MD5). Expõe window.Ants (e window.AntsUI) com a mesma superfície
 * do protótipo de design, mas cada método fala com o BACKEND/DOM REAIS e cada
 * evento nasce de algo que a colônia de verdade fez — não há simulação aqui.
 *
 * Dois sentidos:
 *   IA → UI : Ants.send / say / runFlow / setColonyState / goTo / pushConsole
 *             / setMetric / setCognition / toast / addBot / updateBot
 *   UI → IA : Ants.on('goal'|'flowComplete'|'stateChange'|'online'|'netcall'
 *             |'ready', cb) — alimentado pelos CustomEvents que api_bridge.js
 *             e live_panels.js emitem a partir dos dados reais.
 *
 * "de acordo com o que a IA reagir": o bloco REACTIVE liga a atividade real
 * da colônia à interface viva (estado/pulso mudam quando a IA trabalha).
 */
(function () {
  "use strict";
  var bus = new EventTarget();
  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c];
    });
  };

  var STATE_PT = {
    dormant: "Adormecida", observing: "Observando", exploring: "Explorando",
    building: "Construindo", verifying: "Verificando", learning: "Aprendendo",
    executing: "Executando",
  };

  var api = {
    version: "6.2",
    get state() {
      var app = $("app");
      return app ? app.getAttribute("data-colony-state") : null;
    },

    // ---- IA → UI (ações reais) ----------------------------------------
    send: function (text) {
      var input = $("chat-input"), btn = $("chat-send");
      if (input && btn) {
        input.value = text;
        emit("goal", text);
        btn.click(); // dispara o POST /hive/task REAL via chat.js
      }
      return api;
    },
    runFlow: function (goal) { return api.send(goal || "pesquisa"); },
    say: function (html, meta) {
      var box = $("messages") || $("chat-messages");
      if (!box) return api;
      var el = document.createElement("div");
      el.className = "msg bot message-bot";
      el.innerHTML =
        '<div class="lead"><svg class="ico sm"><use href="#i-ant"/></svg> ' +
        "Colônia Ant's</div>" + (html || "") +
        (meta ? '<div class="msg-meta"><span>' + esc(meta) + "</span></div>" : "");
      box.appendChild(el);
      box.scrollTop = box.scrollHeight;
      return api;
    },
    setColonyState: function (s) {
      var app = $("app");
      if (app) app.setAttribute("data-colony-state", s);
      if ($("state-ind")) $("state-ind").textContent = STATE_PT[s] || s;
      emit("stateChange", s);
      return api;
    },
    goTo: function (tab) {
      if (window.AntUI && window.AntUI.showTab) window.AntUI.showTab(tab);
      else { var b = document.querySelector('.nav-item[data-tab="' + tab + '"]'); if (b) b.click(); }
      return api;
    },
    pushConsole: function (lvl, caste, msg) {
      var box = $("console-log"); if (!box) return api;
      var ln = document.createElement("div");
      ln.className = "ln " + (lvl || "info");
      var ts = new Date().toTimeString().slice(0, 8);
      ln.innerHTML = '<span class="lt">' + ts + '</span><span class="lc">[' +
        esc(caste || "hive") + ']</span><span class="lm">' + esc(msg) + "</span>";
      box.appendChild(ln);
      if (box.children.length > 200) box.removeChild(box.firstChild);
      box.scrollTop = box.scrollHeight;
      return api;
    },
    setMetric: function (k, v) {
      var f = $("mf-" + k), x = $("mv-" + k);
      if (f) f.style.width = v + "%";
      if (x) x.textContent = ("" + v).replace(/%?$/, "%");
      return api;
    },
    setCognition: function (k, pct) {
      var f = $("cf-" + k), p = $("cp-" + k);
      if (f) f.style.width = pct + "%";
      if (p) p.textContent = pct + "%";
      return api;
    },
    toast: function (m) {
      var t = $("toast"); if (!t) return api;
      t.textContent = m; t.classList.add("show");
      clearTimeout(api._tt);
      api._tt = setTimeout(function () { t.classList.remove("show"); }, 2400);
      return api;
    },
    // Ações de dispositivo passam pela guarda imunológica REAL antes de agir.
    guardedAction: function (action) {
      if (!window.AntAPI) return Promise.reject(new Error("offline"));
      return window.AntAPI.post("/organism/immune/analyze", { action: action })
        .then(function (r) { emit("immune", r); return r; });
    },

    // ---- bots (refletem no grid real, se existir) ---------------------
    addBot: function (b) { emit("botAdded", b || {}); return api; },
    updateBot: function (name, patch) { emit("botUpdated", { name: name, patch: patch }); return api; },

    // ---- UI → IA (event bus, alimentado por eventos REAIS) ------------
    on: function (evt, cb) { bus.addEventListener(evt, function (e) { cb(e.detail); }); return api; },
    emit: function (evt, detail) { emit(evt, detail); return api; },
    // A IA modifica a interface por comandos declarativos seguros (UI Kernel).
    ui: function (cmd) { if (window.AntsKernel) window.AntsKernel.apply(cmd); return api; },
  };

  function emit(evt, detail) { bus.dispatchEvent(new CustomEvent(evt, { detail: detail })); }

  // ---- REACTIVE: liga os eventos REAIS do backend ao barramento --------
  // api_bridge.js já dispara estes CustomEvents a partir de dados reais.
  document.addEventListener("ants:task-done", function (e) {
    var st = (e && e.detail) || {}, r = st.result || {};
    emit("flowComplete", {
      goal: st.goal, answer: r.answer, confidence: r.confidence,
      cognition: r.cognition || null, sources: (r.sources || []).length,
      recruitment: r.recruitment || null,
    });
    // Transparência §3.3: "quem chamou quem" no console, a partir do real.
    (r.recruitment || []).slice(0, 8).forEach(function (l) {
      api.pushConsole("info", l.caller, "recrutou " + l.called + " · " + l.reason);
    });
    // A colônia terminou de pensar → volta a observar (interface reage).
    api.setColonyState("observing");
  });
  document.addEventListener("ants:online", function (e) {
    emit("online", !!(e && e.detail));
    if (e && e.detail === false) api.setColonyState("dormant");
  });
  document.addEventListener("ants:netcall", function (e) { emit("netcall", e && e.detail); });

  window.Ants = window.AntsUI = api;
  emit("ready", { version: "6.2" });
  document.dispatchEvent(new CustomEvent("ants:bridge-ready"));
  console.info("%c[Ant's] window.Ants pronto — ponte IA↔UI real",
    "color:#6aa15a;font-weight:bold");
})();
