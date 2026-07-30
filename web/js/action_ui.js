/* Ant's — action_ui.js (8.1 · C): plano de ação no chat com aprovação.
 * Quando a colônia reconhece um COMANDO DE AÇÃO, mostra no chat:
 *  - se falta permissão → botão "Conceder permissão" (liga o escopo certo);
 *  - se há plano → "Aprovar / Ajustar / Cancelar" (executa via /hive/action).
 * Dados reais; zero emoji (SVG). Não toca nos 4 JS legados. */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var A = function () { return window.AntAPI; };
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c];
    });
  };

  function panel() {
    var box = $("action-panel"); if (!box) return null;
    var el = box.querySelector(".act-panel");
    if (!el) { el = document.createElement("div"); el.className = "act-panel"; box.appendChild(el); }
    return el;
  }
  function clearPanel() { var b = $("action-panel"); if (b) b.innerHTML = ""; }

  function toast(m) { if (window.Ants && window.Ants.toast) window.Ants.toast(m); }

  function renderPermission(pv) {
    var el = panel(); if (!el) return;
    var need = [];
    if (pv.grant_scope) need.push("permissão <b>" + esc(pv.grant_scope) + "</b>");
    if (pv.grant_path) need.push("autorizar <b>" + esc(pv.grant_path) + "</b>");
    el.innerHTML = '<div class="act-need"><svg class="ico sm"><use href="#i-shield"/></svg> Falta: ' +
      need.join(" e ") + ".</div>" +
      '<button class="btn act-grant" data-s="' + esc(pv.grant_scope || "") +
      '" data-p="' + esc(pv.grant_path || "") + '">' +
      '<svg class="ico sm"><use href="#i-check"/></svg> Conceder e autorizar</button>';
  }

  function renderApproval(pv) {
    var el = panel(); if (!el) return;
    el.innerHTML = '<div class="act-buttons">' +
      '<button class="btn act-approve" data-p="' + esc(pv.plan_id) + '">' +
      '<svg class="ico sm"><use href="#i-check"/></svg> Aprovar</button>' +
      '<button class="btn ghost act-adjust"><svg class="ico sm"><use href="#i-search"/></svg> Ajustar</button>' +
      '<button class="btn ghost act-cancel" data-p="' + esc(pv.plan_id) + '">' +
      '<svg class="ico sm"><use href="#i-x"/></svg> Cancelar</button></div>' +
      '<div class="act-result"></div>';
  }

  document.addEventListener("ants:task-done", function (e) {
    var st = e.detail || {}; var pv = (st.result || {}).provenance || {};
    if (pv.intent !== "action_device") { clearPanel(); return; }
    clearPanel();
    if (pv.needs_permission) renderPermission(pv);
    else if (pv.needs_approval) renderApproval(pv);
  });

  document.addEventListener("click", function (e) {
    var t = e.target.closest && e.target.closest(".act-grant, .act-approve, .act-cancel, .act-adjust");
    if (!t || !A()) return;
    if (t.classList.contains("act-grant")) {
      var jobs = [];
      if (t.dataset.s) jobs.push(A().post("/device/scopes/grant", { scope: t.dataset.s }));
      if (t.dataset.p) jobs.push(A().post("/device/paths/allow", { path: t.dataset.p }));
      Promise.all(jobs).then(function () {
        toast("Concedido — repita o comando");
        t.closest(".act-panel").innerHTML = '<div class="act-need"><svg class="ico sm"><use href="#i-check"/></svg> Concedido. Repita o comando para executar.</div>';
      });
    } else if (t.classList.contains("act-adjust")) {
      var inp = $("chat-input"); if (inp) inp.focus();
    } else if (t.classList.contains("act-cancel")) {
      A().post("/hive/action/cancel", { plan_id: t.dataset.p }).then(function () {
        t.closest(".act-panel").innerHTML = '<div class="act-need">Ação cancelada.</div>';
      });
    } else if (t.classList.contains("act-approve")) {
      var box = t.closest(".act-panel");
      t.disabled = true; t.textContent = "Executando…";
      A().post("/hive/action/approve", { plan_id: t.dataset.p }).then(function (r) {
        var out = box.querySelector(".act-result");
        var ok = r.executed;
        out.innerHTML = '<div class="act-done ' + (ok ? "ok" : "err") + '"><svg class="ico sm"><use href="#' +
          (ok ? "i-check" : "i-x") + '"/></svg> ' + esc(r.answer || "") + "</div>";
        var btns = box.querySelector(".act-buttons"); if (btns) btns.remove();
      }).catch(function () { t.disabled = false; t.textContent = "Aprovar"; });
    }
  });
})();
