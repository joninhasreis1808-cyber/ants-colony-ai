/* Ant's — device_panel.js (8.0 · D.2): painel de permissões, pânico, auditoria.
 * Dados REAIS de /device/*. Concede/revoga escopos, autoriza pastas, mostra o
 * selo de runtime (web planeja · nativo age), botão de pânico sempre visível e
 * a trilha de auditoria. Zero emoji (SVG). Não toca nos 4 JS legados. */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var A = function () { return window.AntAPI; };
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c];
    });
  };
  var LABEL = {
    read_files: "Ler arquivos", write_files: "Escrever/mover/apagar arquivos",
    run_apps: "Abrir/fechar apps", control_input: "Controlar mouse/teclado",
    screen_capture: "Capturar a tela", system_commands: "Comandos de sistema",
    network: "Acesso à rede",
  };

  async function loadRuntime() {
    if (!A()) return;
    try {
      var d = await A().get("/device/runtime");
      var seal = $("runtime-seal"); if (seal) seal.textContent = "· " + d.label;
    } catch (e) {}
  }

  async function loadScopes() {
    var box = $("device-scopes"); if (!box || !A()) return;
    try {
      var d = await A().get("/device/scopes");
      box.innerHTML = Object.keys(d.scopes).map(function (k) {
        var s = d.scopes[k];
        var extra = s.expires_in != null ? " (" + s.expires_in + "s)" : "";
        return '<div class="set-row"><span class="srl"><span class="t">' + esc(LABEL[k] || k) +
          '</span><span class="d mono">' + esc(k) + extra + "</span></span>" +
          '<label class="switch"><input type="checkbox" class="dev-scope" data-s="' + esc(k) + '"' +
          (s.granted ? " checked" : "") + '/><span class="sl"></span></label></div>';
      }).join("");
      box.querySelectorAll(".dev-scope").forEach(function (cb) {
        cb.addEventListener("change", function () {
          var path = cb.checked ? "/device/scopes/grant" : "/device/scopes/revoke";
          A().post(path, { scope: cb.dataset.s }).then(loadScopes);
        });
      });
    } catch (e) {}
  }

  async function loadPaths() {
    var box = $("dev-paths-list"); if (!box || !A()) return;
    try {
      var d = await A().get("/device/paths");
      box.innerHTML = (d.allowed || []).length
        ? d.allowed.map(function (p) {
            return '<div>' + esc(p) + ' <a href="#" class="dev-path-rm" data-p="' + esc(p) + '">remover</a></div>';
          }).join("")
        : "Nenhuma pasta autorizada.";
      box.querySelectorAll(".dev-path-rm").forEach(function (a) {
        a.addEventListener("click", function (e) {
          e.preventDefault();
          A().post("/device/paths/disallow", { path: a.dataset.p }).then(loadPaths);
        });
      });
    } catch (e) {}
  }

  async function loadAudit() {
    var box = $("device-audit"); if (!box || !A()) return;
    try {
      var d = await A().get("/device/audit?limit=40");
      var rows = d.entries || [];
      box.innerHTML = rows.length ? rows.map(function (e) {
        return '<div class="ln ' + (e.result === "ok" ? "ok" : "err") + '"><span class="lt">' +
          new Date((e.ts || 0) * 1000).toLocaleTimeString() + '</span><span class="lc">' +
          esc(e.action) + '</span><span class="lm">' + esc(e.scope || "") + " · " + esc(e.result) +
          (e.changed ? " · alterou" : "") + "</span></div>";
      }).join("") : '<div class="ln info"><span class="lm">Sem ações registradas.</span></div>';
    } catch (e) {}
  }

  function wire() {
    var add = $("dev-path-add"), inp = $("dev-path-input");
    if (add && inp) add.addEventListener("click", function () {
      var v = (inp.value || "").trim(); if (!v || !A()) return;
      A().post("/device/paths/allow", { path: v }).then(function (r) {
        if (!r.allowed && window.Ants) window.Ants.toast("Caminho recusado (blacklist)");
        inp.value = ""; loadPaths();
      });
    });
    var rev = $("dev-revoke-all");
    if (rev) rev.addEventListener("click", function () {
      if (A()) A().post("/device/scopes/revoke_all", {}).then(loadScopes);
    });
    var exp = $("dev-audit-export");
    if (exp) exp.addEventListener("click", function () {
      if (!A()) return;
      A().get("/device/audit/export").then(function (d) {
        var a = document.createElement("a");
        a.href = URL.createObjectURL(new Blob([d.jsonl || ""], { type: "application/x-ndjson" }));
        a.download = "ants-device-audit-" + Date.now() + ".jsonl"; a.click();
        URL.revokeObjectURL(a.href);
      });
    });
    // Botão de pânico: para tudo, revoga escopos, e reseta ao confirmar.
    var panic = $("panic-button");
    if (panic) panic.addEventListener("click", function () {
      if (!A()) return;
      if (panic.classList.contains("engaged")) {
        A().post("/device/panic/reset", {}).then(function () {
          panic.classList.remove("engaged"); refresh();
        });
      } else {
        A().post("/device/panic", { reason: "botão de pânico" }).then(function () {
          panic.classList.add("engaged");
          if (window.Ants) window.Ants.toast("Colônia congelada — clique de novo para retomar");
          refresh();
        });
      }
    });
  }

  function refresh() { loadRuntime(); loadScopes(); loadPaths(); loadAudit(); }
  document.addEventListener("ants:tab", function (e) { if (e.detail === "settings") refresh(); });
  function init() { wire(); refresh(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
