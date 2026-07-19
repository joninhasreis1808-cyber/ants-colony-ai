/* Ant's — controls.js: liga botões antes decorativos ao backend REAL.
 * Aditivo; não toca nos 4 JS protegidos (chat/bots/memory/factory).
 *
 * §3.4  Autonomia (seg) → GET/POST /colony/autonomy (durável, com motivo).
 * §4.4  Card do observador → GET /organism/observer (achados reais, 3x/dia).
 * §4.5  Guarda imunológica → POST /organism/immune/analyze antes de agir;
 *       ação perigosa exige confirmação em destaque vermelho.
 */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var A = function () { return window.AntAPI; };

  // ---- estilos auto-injetados (coesos com o design, sem emojis) --------
  var css = document.createElement("style");
  css.textContent =
    ".btn:disabled,.btn.ghost:disabled{opacity:.45;cursor:not-allowed;filter:grayscale(.3)}" +
    "#observer-card{position:fixed;right:18px;bottom:96px;max-width:340px;z-index:70;" +
    "background:var(--surface,#1e1810);border:1px solid var(--border2,#4a3c24);" +
    "border-left:3px solid var(--amber,#d4a017);border-radius:10px;padding:14px 15px;" +
    "box-shadow:0 10px 30px rgba(0,0,0,.45);font-size:13.5px;display:none}" +
    "#observer-card.show{display:block;animation:rise .35s ease both}" +
    "#observer-card .oc-h{font-family:var(--mono,monospace);font-size:10px;letter-spacing:.14em;" +
    "text-transform:uppercase;color:var(--dim,#7a6e58);margin-bottom:8px;display:flex;gap:8px;align-items:center}" +
    "#observer-card .oc-actions{display:flex;gap:8px;margin-top:12px}" +
    "#observer-card .oc-actions button{flex:1;min-height:40px;border-radius:9px;font-family:var(--mono,monospace);" +
    "font-size:12px;cursor:pointer;border:1px solid var(--border2,#4a3c24);background:var(--bg2,#161209);color:var(--text,#ece3d2)}" +
    "#observer-card .oc-actions .allow{border-color:var(--leaf,#6aa15a);color:var(--leaf,#6aa15a)}" +
    ".immune-danger{border-left-color:var(--soldier,#c25a4e)!important}" +
    ".immune-danger .oc-h{color:var(--soldier,#c25a4e)}";
  document.head.appendChild(css);

  // ---- §3.4 Autonomia real + persistente -------------------------------
  var POLICIES = ["cautious", "supervised", "autonomous"]; // ordem dos botões
  function paintAutonomy(policy) {
    var seg = $("autonomy-seg"); if (!seg) return;
    var btns = seg.querySelectorAll("button");
    btns.forEach(function (b, i) { b.classList.toggle("on", POLICIES[i] === policy); });
  }
  function loadAutonomy() {
    if (!A()) return;
    A().get("/colony/autonomy").then(function (r) {
      window.__antAutonomy = r.policy;
      paintAutonomy(r.policy);
    }).catch(function () {});
  }
  function wireAutonomy() {
    var seg = $("autonomy-seg"); if (!seg || seg._w) return; seg._w = true;
    seg.querySelectorAll("button").forEach(function (btn, i) {
      btn.addEventListener("click", function () {
        var policy = POLICIES[i]; if (!A()) return;
        A().post("/colony/autonomy", { policy: policy }).then(function (r) {
          if (r.error) return;
          window.__antAutonomy = r.policy;
          paintAutonomy(r.policy);
          var why = r.confirm_all ? "confirma toda ação"
            : r.block_dangerous ? "bloqueia ações perigosas"
            : "age sem confirmar (ainda sob guarda imunológica)";
          if (window.Ants) window.Ants.toast("Autonomia: " + r.label + " · " + why);
          if (window.Ants) window.Ants.pushConsole("ok", "queen",
            "autonomia → " + r.label + " · " + why);
        }).catch(function () {});
      });
    });
  }

  // ---- §4.4 Card do observador (consultivo, não-invasivo) --------------
  function dayKey() { return "ant-observer-" + new Date().toISOString().slice(0, 10); }
  function shownToday() { return parseInt(localStorage.getItem(dayKey()) || "0", 10); }
  function bumpToday() { localStorage.setItem(dayKey(), String(shownToday() + 1)); }

  function showObserver(f, suggestion) {
    if (shownToday() >= 3) return;              // máx 3x/dia (não incomodar)
    var card = $("observer-card");
    if (!card) {
      card = document.createElement("div"); card.id = "observer-card";
      document.body.appendChild(card);
    }
    card.className = (f.severity === "alert" || f.severity === "warning") ? "show" : "show";
    card.innerHTML =
      '<div class="oc-h"><svg class="ico sm" style="color:var(--amber)"><use href="#i-search"/></svg> Observador da colônia</div>' +
      '<div>' + esc(f.message) + "</div>" +
      (suggestion ? '<div style="color:var(--muted);margin-top:6px;font-size:12.5px">' + esc(suggestion) + "</div>" : "") +
      '<div class="oc-actions"><button class="allow" id="oc-allow">Permitir</button>' +
      '<button id="oc-ignore">Ignorar</button></div>';
    bumpToday();
    $("oc-allow").onclick = function () {
      if (window.Ants) window.Ants.pushConsole("ok", "observer", "usuário permitiu: " + f.kind);
      card.classList.remove("show");
    };
    $("oc-ignore").onclick = function () {
      if (window.Ants) window.Ants.pushConsole("info", "observer", "usuário ignorou: " + f.kind);
      card.classList.remove("show");
    };
  }
  function pollObserver() {
    if (!A() || shownToday() >= 3) return;
    A().get("/organism/observer").then(function (r) {
      if (r && r.findings && r.findings.length) {
        showObserver(r.findings[0], (r.suggestions || [])[0]);
      }
    }).catch(function () {});
  }

  // ---- §4.5 Guarda imunológica (usada pela ponte window.Ants) ----------
  // Antes de QUALQUER ação de dispositivo, analisa a ameaça; se pedir
  // confirmação, mostra destaque vermelho e só age com o "Confirmar".
  function guardedConfirm(action) {
    return new Promise(function (resolve) {
      if (!A()) return resolve(false);
      A().post("/organism/immune/analyze", { action: action }).then(function (r) {
        var policy = window.__antAutonomy || "supervised";
        var needsConfirm = r.requires_confirmation;
        if (policy === "cautious") needsConfirm = true;   // cautelosa confirma tudo
        if (policy === "autonomous" && !r.dangerous) needsConfirm = false;
        if (!needsConfirm) return resolve(true);
        var card = document.createElement("div");
        card.id = "observer-card"; card.className = "show immune-danger";
        card.innerHTML =
          '<div class="oc-h"><svg class="ico sm"><use href="#i-shield"/></svg> Guarda imunológica · ' + esc(r.level) + "</div>" +
          "<div>A ação <b>" + esc(action) + "</b> foi marcada como <b>" + esc(r.level) +
          "</b>. Confirmar mesmo assim?</div>" +
          '<div class="oc-actions"><button class="allow" id="oc-confirm">Confirmar</button>' +
          '<button id="oc-cancel">Cancelar</button></div>';
        document.body.appendChild(card);
        $("oc-confirm").onclick = function () { card.remove(); resolve(true); };
        $("oc-cancel").onclick = function () { card.remove(); resolve(false); };
      }).catch(function () { resolve(false); });
    });
  }
  window.AntGuard = { confirm: guardedConfirm };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c];
    });
  }

  // ---- init ------------------------------------------------------------
  function init() {
    wireAutonomy(); loadAutonomy();
    document.querySelectorAll('.nav-item[data-tab="settings"]').forEach(function (b) {
      b.addEventListener("click", loadAutonomy);
    });
    // Observer roda quando a colônia está viva; espera a ponte/health.
    document.addEventListener("ants:online", function (e) { if (e.detail) setTimeout(pollObserver, 1500); });
    setTimeout(pollObserver, 4000);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
