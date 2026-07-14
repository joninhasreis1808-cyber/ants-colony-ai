/* Ant's — scripts.js: SOMENTE animações/UI e pontes de compatibilidade.
   Não contém lógica de negócio. Garante que a interface nova acione os
   arquivos originais (chat.js, bots.js, memory.js, factory.js) sem alterá-los. */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);

  /* ---- Navegação entre abas + título dinâmico ---- */
  const TAB = { chat: "Chat", bots: "Bots", memory: "Memória",
                factory: "App Factory", colony: "Colônia", settings: "Ajustes" };
  const TAB_ICON = { chat: "i-chat", bots: "i-bots", memory: "i-mem",
                     factory: "i-factory", colony: "i-crown", settings: "i-settings" };
  function showTab(name) {
    document.querySelectorAll(".tab").forEach((t) =>
      t.classList.toggle("active", t.id === "tab-" + name));
    document.querySelectorAll(".nav-item").forEach((b) =>
      b.classList.toggle("active", b.dataset.tab === name));
    const tt = $("topbar-title");
    if (tt) {
      tt.innerHTML = '<svg class="ico"><use href="#' + TAB_ICON[name] +
        '"/></svg>' + TAB[name];
    }
    // aciona os hooks dos módulos originais (sem alterá-los)
    if (name === "memory" && window.Memory) window.Memory.refresh();
    if (name === "settings" && window.Ant) window.Ant.showHealth();
  }
  document.querySelectorAll(".nav-item").forEach((b) =>
    b.addEventListener("click", () => showTab(b.dataset.tab)));

  /* ---- Pontes de compatibilidade (campo visível -> ID legado) ----
     A UI nova usa IDs descritivos; os .js originais leem os IDs antigos.
     Espelhamos o valor em tempo real, sem tocar nos .js. */
  function bridge(visibleId, legacyId, ev) {
    const vis = $(visibleId), leg = $(legacyId);
    if (!vis || !leg) return;
    vis.addEventListener(ev || "input", () => { leg.value = vis.value; });
  }
  bridge("factory-description", "fac-desc");
  bridge("factory-template", "fac-template", "change");

  /* Factory: o botão visível dispara o botão legado que factory.js escuta. */
  const facBtn = $("factory-create"), facLegacy = $("fac-create");
  if (facBtn && facLegacy) {
    facBtn.addEventListener("click", () => {
      $("fac-desc").value = ($("factory-description") || {}).value || "";
      $("fac-template").value = ($("factory-template") || {}).value || "";
      facLegacy.click();
    });
  }

  /* ---- Tema: app.js já cuida do #theme-toggle; não duplicar aqui. ---- */

  /* ---- Modal de visão do bot: abrir/fechar ---- */
  const modal = $("bot-vision-modal");
  function openBotVision(name, caste) {
    if (!modal) return;
    if (name) $("bot-vision-name").textContent = name;
    if (caste) $("bot-vision-caste").textContent = caste;
    modal.classList.add("show");
  }
  function closeBotVision() { modal && modal.classList.remove("show"); }
  ["bot-vision-close", "bot-vision-stop"].forEach((id) => {
    const el = $(id); if (el) el.addEventListener("click", closeBotVision);
  });
  if (modal) modal.addEventListener("click", (e) => {
    if (e.target === modal) closeBotVision();
  });
  // clicar num card de bot abre a visão (delegação; cards são dinâmicos)
  document.addEventListener("click", (e) => {
    const card = e.target.closest && e.target.closest(".bot-card");
    if (card) {
      const nm = card.querySelector(".name");
      const cs = card.querySelector(".bot-caste");
      openBotVision(nm ? nm.textContent : "Bot", cs ? cs.textContent : "");
    }
  });
  window.AntUI = { openBotVision, closeBotVision, showTab };

  /* ---- Painel de progresso (estilo Manus), dirigível por UI ----
     API visual pura: AntUI.progress.start(steps) / advance() / fail().
     Não faz chamadas de rede; apenas reflete o andamento na tela. */
  const PP = {
    _t0: 0, _timer: null,
    start(title, steps) {
      const panel = $("progress-panel");
      if (!panel) return;
      panel.style.display = "";
      const list = $("progress-steps");
      list.innerHTML = "";
      this._steps = steps.slice();
      steps.forEach((s, i) => {
        const el = document.createElement("div");
        el.className = "step pending";
        el.id = "pstep-" + i;
        el.innerHTML = '<span class="st-ico"><svg class="ico ico-sm"><use href="#i-clock"/></svg></span>' +
          '<div class="st-body"><div class="st-lbl">' + s.lbl + '</div>' +
          '<div class="st-desc"></div></div><span class="st-time"></span>';
        list.appendChild(el);
      });
      $("progress-bar").style.width = "0%";
      $("progress-pct").textContent = "0%";
      this._t0 = Date.now();
      this._timer = setInterval(() => {
        const s = ((Date.now() - this._t0) / 1000).toFixed(1);
        const el = $("progress-elapsed"); if (el) el.textContent = s + "s";
      }, 100);
    },
    step(i, state, desc, bot) {
      const el = $("pstep-" + i);
      if (!el) return;
      el.className = "step " + state;
      const ico = state === "done" ? "i-check" : state === "failed" ? "i-x" :
        state === "running" ? "i-loader" : "i-clock";
      const svg = el.querySelector(".st-ico");
      svg.innerHTML = '<svg class="ico ico-sm' +
        (state === "running" ? " spin" : "") + '"><use href="#' + ico + '"/></svg>';
      if (desc) el.querySelector(".st-desc").textContent = desc;
      if (state === "done" || state === "failed")
        el.querySelector(".st-time").textContent =
          ((Date.now() - this._t0) / 1000).toFixed(1) + "s";
      const pct = Math.round(((i + (state === "done" ? 1 : 0)) /
        this._steps.length) * 100);
      $("progress-bar").style.width = pct + "%";
      $("progress-pct").textContent = pct + "%";
      if (bot) { const b = $("progress-active-bot"); if (b) b.textContent = bot; }
      el.scrollIntoView({ behavior: "smooth", block: "nearest" });
    },
    finish(ok) {
      clearInterval(this._timer);
      $("progress-pct").textContent = ok ? "100%" : "interrompido";
      if (ok) $("progress-bar").style.width = "100%";
    },
    hide() { const p = $("progress-panel"); if (p) p.style.display = "none"; },
  };
  window.AntUI.progress = PP;

  const minBtn = $("progress-minimize");
  if (minBtn) minBtn.addEventListener("click", () => {
    PP.hide();
    const f = $("floating-progress");
    if (f) f.classList.add("show");
  });

  /* ---- Indicador flutuante de progresso ---- */
  const floating = $("floating-progress");
  if (floating) floating.addEventListener("click", () => {
    floating.classList.remove("show");
    const pp = document.querySelector(".progress-panel");
    if (pp) pp.scrollIntoView({ behavior: "smooth", block: "center" });
  });
})();
