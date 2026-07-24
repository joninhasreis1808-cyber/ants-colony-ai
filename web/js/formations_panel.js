/* Ant's — formations_panel.js (7.2 · Bloco C): as formações vivas na Cognição.
 * Dados REAIS de GET /hive/formations. Para cada formação: nome + objetivo;
 * para cada bot: ícone SVG da casta + nome de missão + o que faz agora; sob
 * cada casta, "Recrutar +1" (reinforce) e "Dispensar -1" (release, nunca < 1,
 * desabilita em 1). Ao concluir: "Missão concluída — enviada para o Chat" e o
 * X para descartar (só após conclusão). Sem emoji; só SVG. Não toca legados. */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var A = function () { return window.AntAPI; };
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c];
    });
  };
  var ICON = { exploradores: "i-compass", construtores: "i-cpu",
               coletores: "i-book", costureiros: "i-colony",
               operarias: "i-worker", soldados: "i-shield" };

  function botRow(b) {
    return '<div class="fm-bot ' + esc(b.caste) + '">' +
      '<svg class="ico sm"><use href="#' + (ICON[b.caste] || "i-ant") + '"/></svg>' +
      '<span class="fm-handle">' + esc(b.handle) + '</span>' +
      '<span class="fm-doing">' + esc(b.doing) + '</span></div>';
  }

  function casteControls(fid, caste, count) {
    var atMin = count <= 1;
    return '<div class="fm-ctl">' +
      '<span class="fm-caste">' + esc(caste) + ' ×' + count + '</span>' +
      '<button class="btn ghost fm-plus" data-f="' + esc(fid) + '" data-c="' + esc(caste) + '">' +
      '<svg class="ico sm"><use href="#i-check"/></svg> Recrutar +1</button>' +
      '<button class="btn ghost fm-minus" data-f="' + esc(fid) + '" data-c="' + esc(caste) + '"' +
      (atMin ? ' disabled title="nunca abaixo de 1"' : "") + '>' +
      '<svg class="ico sm"><use href="#i-x"/></svg> Dispensar -1</button></div>';
  }

  function card(f) {
    var counts = f.counts || {};
    var done = f.status === "done";
    var ctls = Object.keys(counts).map(function (c) {
      return casteControls(f.id, c, counts[c]);
    }).join("");
    var bots = (f.bots || []).map(botRow).join("");
    var head = '<div class="fm-head"><span class="fm-name">' + esc(f.name) + '</span>' +
      (done ? '<button class="fm-x" data-f="' + esc(f.id) + '" title="Descartar formação">' +
        '<svg class="ico sm"><use href="#i-x"/></svg></button>' : "") + '</div>' +
      '<div class="fm-goal mono">' + esc(f.goal) + '</div>';
    var footer = done
      ? '<div class="fm-done"><svg class="ico sm"><use href="#i-check"/></svg> Missão concluída — enviada para o Chat</div>'
      : "";
    return '<div class="fm-card">' + head + '<div class="fm-bots">' + bots + "</div>" +
      '<div class="fm-ctls">' + ctls + "</div>" + footer + "</div>";
  }

  async function load() {
    var box = $("formations-panel"); if (!box || !A()) return;
    try {
      var d = await A().get("/hive/formations");
      var fs = d.formations || [];
      box.innerHTML = fs.length ? fs.map(card).join("")
        : '<div class="mono" style="color:var(--dim);font-size:12.5px">Nenhuma formação ativa — envie um objetivo no Chat.</div>';
    } catch (e) { /* adormecida: mantém o texto atual */ }
  }

  // ações (delegação) — chamam os endpoints reais e recarregam
  document.addEventListener("click", function (e) {
    var t = e.target.closest && e.target.closest(".fm-plus, .fm-minus, .fm-x");
    if (!t || !A()) return;
    var fid = t.dataset.f, caste = t.dataset.c;
    var p;
    if (t.classList.contains("fm-plus")) p = A().post("/hive/formation/" + fid + "/reinforce", { caste: caste });
    else if (t.classList.contains("fm-minus")) p = A().post("/hive/formation/" + fid + "/release", { caste: caste });
    else p = fetch(location.origin + "/hive/formation/" + fid, { method: "DELETE" });
    Promise.resolve(p).then(load).catch(load);
  });

  // recarrega quando a Cognição abre e quando uma tarefa conclui
  document.addEventListener("ants:tab", function (e) { if (e.detail === "cognitive") load(); });
  document.addEventListener("ants:task-done", function () { setTimeout(load, 300); });
  setInterval(function () {
    if (document.querySelector("#tab-cognitive.is-active, #tab-cognitive.active")) load();
  }, 5000);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", load); else load();
})();
