/* Ant's — ui_kernel.js: a IA modifica a interface DENTRO de uma fronteira segura.
 * O backend/ponte emite comandos DECLARATIVOS; o kernel valida e aplica.
 * Conjunto FECHADO de ações — comando inválido é ignorado com log, NUNCA
 * executa HTML arbitrário. Aditivo; não toca nos JS protegidos.
 *
 * Uso:  window.AntsKernel.apply({action:"highlight", target:"explorer", reason:"…"})
 *       window.AntsKernel.applyMany([...])
 * A ponte também escuta o evento "ants:ui" e aplica o detalhe.
 */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); };
  function log(msg, cmd) { try { console.warn("[AntsKernel] " + msg, cmd); } catch (e) {} }

  var CASTES = { queen: "caste-queen", rainha: "caste-queen", explorer: "caste-explorer", exploradora: "caste-explorer",
    worker: "caste-worker", operaria: "caste-worker", soldier: "caste-soldier", soldado: "caste-soldier",
    gardener: "caste-gardener", jardineira: "caste-gardener", nurse: "caste-nurse", cuidadora: "caste-nurse" };
  var STATES = ["dormant", "observing", "exploring", "building", "verifying", "learning", "defending", "executing"];

  // Cada ação é uma função pura sobre o DOM. Nada fora deste mapa roda.
  var ACTIONS = {
    highlight: function (c) {
      // realça um integrante/seção por um instante (feedback visual seguro)
      var el = $("th-flow") || document.body;
      var cls = CASTES[String(c.target || "").toLowerCase()] || "caste-worker";
      var tag = document.createElement("div");
      tag.className = "kernel-flash " + cls;
      tag.textContent = (c.target || "colônia") + (c.reason ? " · " + c.reason : "");
      el.prepend(tag);
      setTimeout(function () { tag.remove(); }, 3000);
      return true;
    },
    update_progress: function (c) {
      var p = Math.max(0, Math.min(100, Number(c.progress)));
      if (isNaN(p)) return false;
      var bar = $("flow-pct"); if (bar) bar.textContent = p + "%";
      document.dispatchEvent(new CustomEvent("ants:task-tick", { detail: { pct: p, done: p >= 100 } }));
      return true;
    },
    open_section: function (c) {
      var t = String(c.target || "");
      var map = { console: "console", missions: "missions", registro: "registro", timeline: "registro" };
      var sec = map[t]; if (!sec) return false;
      var btn = document.querySelector('.nav-item[data-tab="timeline"]'); if (btn) btn.click();
      var sub = document.querySelector('.th-tab[data-sec="' + sec + '"]'); if (sub) sub.click();
      return true;
    },
    close_section: function () { var b = document.querySelector('.nav-item[data-tab="chat"]'); if (b) b.click(); return true; },
    append_timeline: function (c) {
      var box = $("decision-timeline"); if (!box) return false;
      var cls = CASTES[String(c.caste || "").toLowerCase()] || "caste-worker";
      var row = document.createElement("div");
      row.className = cls;
      row.style.cssText = "display:flex;align-items:center;gap:10px;padding:9px 12px;border-left:2px solid var(--caste);margin-bottom:5px;background:var(--ant-bg-surface);border-radius:0 8px 8px 0";
      var t = new Date((c.ts ? c.ts * 1000 : Date.now())).toLocaleTimeString().slice(0, 5);
      row.innerHTML = '<span style="font-size:11px;color:var(--ant-text-secondary);min-width:42px">' + t +
        '</span><svg class="ico ico-sm" style="color:var(--caste)"><use href="#i-ant"/></svg><span style="font-size:13px">' + esc(c.text || "") + "</span>";
      if (box.firstChild && box.firstChild.textContent && /adormecida|sem eventos/i.test(box.firstChild.textContent)) box.innerHTML = "";
      box.insertBefore(row, box.firstChild);
      return true;
    },
    set_state: function (c) {
      var s = String(c.target || c.state || "");
      if (STATES.indexOf(s) < 0) return false;
      if (window.Ants) window.Ants.setColonyState(s); return true;
    },
    toast: function (c) { if (window.Ants) window.Ants.toast(String(c.text || c.message || "")); return true; },
  };

  function apply(cmd) {
    if (!cmd || typeof cmd !== "object" || typeof cmd.action !== "string") { log("comando malformado", cmd); return false; }
    var fn = ACTIONS[cmd.action];
    if (!fn) { log("ação desconhecida ignorada: " + cmd.action, cmd); return false; }
    try { var ok = fn(cmd); if (!ok) log("ação recusada (parâmetro inválido): " + cmd.action, cmd); return ok; }
    catch (e) { log("erro ao aplicar " + cmd.action, e); return false; }
  }
  function applyMany(list) { return (Array.isArray(list) ? list : []).map(apply); }

  window.AntsKernel = { apply: apply, applyMany: applyMany, actions: Object.keys(ACTIONS) };
  // A ponte/IA pode emitir comandos por evento, sem acesso direto ao DOM.
  document.addEventListener("ants:ui", function (e) {
    var d = e.detail; if (Array.isArray(d)) applyMany(d); else apply(d);
  });
  try { console.info("%c[AntsKernel] pronto — ações: " + Object.keys(ACTIONS).join(", "), "color:#6aa15a"); } catch (e) {}
})();
