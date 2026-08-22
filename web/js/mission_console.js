/* Ant's — mission_console.js (9.12 · Passo 3): console de Missão Autônoma + Evolução.
 * Dá rosto às duas portas mais poderosas da colônia:
 *  • Missão autônoma (/mission/auto): o laço Observar→Planejar→Agir→Verificar,
 *    mostrando rota, ciclos (decisão/progresso), ferramentas usadas e resposta.
 *  • Evolução controlada (/evolution): minerar propostas da experiência e o dono
 *    aprovar/rejeitar/aplicar — cada aplicação mexe só em dados, nunca em código.
 * Aditivo; usa AntAPI (api_bridge). NÃO toca nos 4 JS legados. Sem emojis.
 * As rotas são owner-gated: em 127.0.0.1 (app do dono) passam; num deploy público
 * exigem token — o console mostra o erro honesto em vez de fingir. */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>]/g,
    function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); };

  function injectStyle() {
    if ($("mission-console-style")) return;
    var s = document.createElement("style");
    s.id = "mission-console-style";
    s.textContent =
      "#mission-console{border:1px solid var(--line,#2a2a2a);border-radius:12px;"
      + "padding:12px 14px;background:var(--card,rgba(255,255,255,.03));margin:14px 0}"
      + "#mission-console h3{font-size:13px;margin:2px 0 8px;color:var(--gold,#d4a017);"
      + "text-transform:uppercase;letter-spacing:.04em}"
      + "#mission-console .mc-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0}"
      + "#mission-console input[type=text]{flex:1;min-width:180px;padding:7px 10px;"
      + "border:1px solid var(--line,#2a2a2a);border-radius:8px;background:transparent;color:inherit}"
      + "#mission-console button{padding:6px 12px;border-radius:8px;border:1px solid var(--line,#2a2a2a);"
      + "background:rgba(212,160,23,.14);color:inherit;cursor:pointer;font-size:12px}"
      + "#mission-console button:disabled{opacity:.5;cursor:default}"
      + "#mission-console label{font-size:12px;color:var(--dim,#9aa);display:flex;gap:4px;align-items:center}"
      + "#mission-console .mc-out{font-size:12px;line-height:1.7;margin-top:8px;white-space:pre-wrap}"
      + "#mission-console .mc-sep{height:1px;background:var(--line,#2a2a2a);margin:12px 0}"
      + "#mission-console .mc-prop{border:1px solid var(--line,#2a2a2a);border-radius:8px;padding:8px 10px;margin:6px 0}"
      + "#mission-console .mc-badge{font-size:11px;padding:1px 7px;border-radius:999px;border:1px solid var(--line,#2a2a2a)}"
      + "#mission-console .mc-err{color:#c0392b}";
    document.head.appendChild(s);
  }

  function build() {
    var el = $("mission-console"); if (!el) return;
    injectStyle();
    el.innerHTML =
      '<h3>Missão autônoma</h3>'
      + '<div class="mc-row"><input type="text" id="mc-goal" '
      + 'placeholder="Objetivo (ex.: quanto é 12 * 12)"/></div>'
      + '<div class="mc-row"><label><input type="checkbox" id="mc-online"/> usar rede</label>'
      + '<label><input type="checkbox" id="mc-deep"/> pesquisa profunda</label>'
      + '<button id="mc-run">Executar</button></div>'
      + '<div class="mc-out" id="mc-out"></div>'
      + '<div class="mc-sep"></div>'
      + '<h3>Evolução da colônia</h3>'
      + '<div class="mc-row"><button id="mc-mine">Minerar propostas</button>'
      + '<button id="mc-refresh">Atualizar lista</button></div>'
      + '<div id="mc-props"></div>';
    $("mc-run").onclick = runMission;
    $("mc-mine").onclick = mineProposals;
    $("mc-refresh").onclick = loadProposals;
    loadProposals();
  }

  function runMission() {
    var goal = ($("mc-goal").value || "").trim();
    var out = $("mc-out");
    if (!goal) { out.innerHTML = '<span class="mc-err">Digite um objetivo.</span>'; return; }
    out.textContent = "a colônia trabalha…";
    $("mc-run").disabled = true;
    AntAPI.post("/mission/auto", {
      goal: goal, online: $("mc-online").checked, deep: $("mc-deep").checked, max_cycles: 3,
    }).then(function (r) {
      var lines = [];
      lines.push("rota final: " + esc((r.final_outcome && r.final_outcome.route
        && r.final_outcome.route.name) || "—") + " · parada: " + esc(r.stop_reason)
        + " · convergiu: " + (r.converged ? "sim" : "não"));
      (r.cycles || []).forEach(function (c) {
        lines.push("  ciclo " + c.n + ": " + esc(c.decision) + " · progresso "
          + Math.round((c.progress || 0) * 100) + "% · " + esc(c.state));
      });
      var tu = (r.final_outcome && r.final_outcome.tools_used) || [];
      if (tu.length) lines.push("ferramentas: " + tu.map(function (t) {
        return t.tool + (t.ok ? " (ok)" : " (recusada)"); }).join(", "));
      if (r.answer) lines.push("\nResposta: " + esc(r.answer));
      out.textContent = lines.join("\n");
    }).catch(function (e) {
      out.innerHTML = '<span class="mc-err">Falha (' + esc(e && e.message)
        + '). Rotas de missão são do dono: rode na sua máquina (127.0.0.1) ou '
        + 'informe o token no deploy público.</span>';
    }).then(function () { $("mc-run").disabled = false; });
  }

  function mineProposals() {
    AntAPI.post("/evolution/mine", {}).then(function () { loadProposals(); })
      .catch(function (e) { showPropsError(e); });
  }

  function loadProposals() {
    AntAPI.get("/evolution").then(function (r) {
      var box = $("mc-props"); if (!box) return;
      var ps = r.proposals || [];
      if (!ps.length) { box.innerHTML = '<div class="mc-out">Sem propostas. '
        + 'Clique em “Minerar” após a colônia acumular experiência.</div>'; return; }
      box.innerHTML = ps.map(function (p) {
        var acts = "";
        if (p.status === "proposed")
          acts = '<button data-act="approve" data-id="' + esc(p.id) + '">Aprovar</button> '
               + '<button data-act="reject" data-id="' + esc(p.id) + '">Rejeitar</button>';
        else if (p.status === "approved")
          acts = '<button data-act="apply" data-id="' + esc(p.id) + '">Aplicar (só dados)</button>';
        return '<div class="mc-prop"><div class="mc-row"><span class="mc-badge">'
          + esc(p.status) + '</span> <b>' + esc(p.title) + '</b></div>'
          + '<div class="mc-out">' + esc(p.rationale) + " · risco " + esc(p.risk)
          + '</div><div class="mc-row">' + acts + "</div></div>";
      }).join("");
      [].slice.call(box.querySelectorAll("button[data-act]")).forEach(function (b) {
        b.onclick = function () {
          AntAPI.post("/evolution/" + b.getAttribute("data-id") + "/"
            + b.getAttribute("data-act"), {}).then(loadProposals)
            .catch(function (e) { showPropsError(e); });
        };
      });
    }).catch(function (e) { showPropsError(e); });
  }

  function showPropsError(e) {
    var box = $("mc-props"); if (!box) return;
    box.innerHTML = '<div class="mc-out mc-err">Falha (' + esc(e && e.message)
      + '). /evolution é owner-gated — rode na sua máquina ou informe o token.</div>';
  }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", build);
  else build();
})();
