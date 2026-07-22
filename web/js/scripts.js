/* Ant's — scripts.js: SOMENTE animações/UI e pontes de compatibilidade.
   Não contém lógica de negócio. Garante que a interface nova acione os
   arquivos originais (chat.js, bots.js, memory.js, factory.js) sem alterá-los. */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);

  /* ---- Navegação entre abas (design usa .tab.is-active) ---- */
  function showTab(name) {
    document.querySelectorAll(".tab").forEach((t) => {
      const on = t.id === "tab-" + name;
      t.classList.toggle("is-active", on);
      t.classList.toggle("active", on);
    });
    document.querySelectorAll(".nav-item").forEach((b) =>
      b.classList.toggle("active", b.dataset.tab === name));
    // aciona os hooks dos módulos originais (sem alterá-los)
    if (name === "environment" && window.Memory) window.Memory.refresh();
    if (name === "settings" && window.Ant) window.Ant.showHealth();
    document.dispatchEvent(new CustomEvent("ants:tab", { detail: name }));
  }
  document.querySelectorAll(".nav-item").forEach((b) =>
    b.addEventListener("click", () => showTab(b.dataset.tab)));

  /* ---- Perfis (Usuário/Dev/Cientista): data-mode no #app ---- */
  const modeSwitch = $("mode-switch");
  if (modeSwitch) modeSwitch.querySelectorAll("button").forEach((btn) =>
    btn.addEventListener("click", () => {
      modeSwitch.querySelectorAll("button").forEach((b) => b.classList.remove("on"));
      btn.classList.add("on");
      const app = $("app");
      if (app) app.setAttribute("data-mode", btn.dataset.mode || "user");
    }));

  /* ---- Tema: settings-theme (visível) <-> theme-toggle (app.js) ---- */
  const setTheme = $("settings-theme"), legacyTheme = $("theme-toggle");
  if (setTheme && legacyTheme) {
    setTheme.checked = legacyTheme.checked ||
      localStorage.getItem("ant-theme") === "light";
    setTheme.addEventListener("change", () => {
      legacyTheme.checked = setTheme.checked;
      legacyTheme.dispatchEvent(new Event("change"));
    });
  }

  /* ---- Conexão: espelha #conn (app.js) -> #connection-indicator (design) ---- */
  const conn = $("conn"), connInd = $("connection-indicator");
  if (conn && connInd) {
    const mirror = () => {
      // Honestidade: só reflete o texto real do #conn; nunca fabrica
      // "Conectado" quando o estado é desconhecido/vazio (§0.6).
      const t = (conn.textContent || "").trim();
      if (t) connInd.textContent = t;
      connInd.classList.toggle("offline", conn.classList.contains("offline"));
    };
    new MutationObserver(mirror).observe(conn,
      { childList: true, characterData: true, subtree: true, attributes: true });
    mirror();
  }
  /* Fonte autoritativa de online/offline: o api_bridge sabe se o backend
     respondeu. Offline => "Adormecida" honesta, nunca "Conectado" falso. */
  if (connInd) {
    const setConn = (ok) => {
      if (ok) { connInd.textContent = "Conectado"; connInd.classList.remove("offline"); }
      else { connInd.textContent = "Adormecida"; connInd.classList.add("offline"); }
    };
    document.addEventListener("ants:online", (e) => setConn(!!e.detail));
    // Caso o api_bridge já saiba o estado antes deste listener existir.
    if (window.AntAPI && window.AntAPI.online != null) setConn(window.AntAPI.online);
  }

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

/* ============================================================
   CAMADA DE EXIBIÇÃO SEM EMOJIS (§0.5) — MD5 dos JS protegidos intacto.
   chat.js / bots.js / factory.js / memory.js (imutáveis) escrevem emojis
   (🐜 ✅ ⚠️ 🤖 ⏳ 😴) no espelho legado. Esta camada, num arquivo LIVRE,
   substitui o emoji por um ícone SVG coeso — SOMENTE nos nós que contêm
   emoji. Conteúdo interativo (botões da saudação, .lead, ações) fica
   intocado. Observadores são ALVO e debounced (rAF) — nada de varrer o
   documento inteiro, para não sobrecarregar a máquina. Auto-cicatriza:
   quando o JS protegido reescreve textContent (streaming), reaplica.
   ============================================================ */
(function noEmojiLayer() {
  "use strict";
  var HAS = /[\u{1F000}-\u{1FAFF}\u{2300}-\u{27BF}\u{2B00}-\u{2BFF}\u{2190}-\u{21FF}\u{FE0F}\u{200D}]/u;
  var STRIP = new RegExp(HAS.source, "gu");
  var strip = function (s) { return (s || "").replace(STRIP, "").replace(/[ \t]{2,}/g, " ").replace(/ *\n */g, "\n").trim(); };
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); };
  var svg = function (id) { return '<svg class="ico sm" aria-hidden="true" style="display:inline-block;vertical-align:-3px"><use href="#' + id + '"/></svg>'; };
  var $ = function (id) { return document.getElementById(id); };

  function iconFor(raw) {
    if (/\u{1F41C}/u.test(raw)) return "i-ant";         // formiga (trabalhando)
    if (/✅/.test(raw)) return "i-check";               // concluído
    if (/[⚠\u{1F6AB}]/u.test(raw)) return "i-shield";   // aviso/erro
    if (/⏳|⌛/.test(raw)) return "i-clock";             // aguardando
    if (/\u{1F634}/u.test(raw)) return "i-moon";        // sono
    if (/\u{1F916}/u.test(raw)) return "i-worker";      // bot
    return null;
  }

  function debounced(fn) {   // rAF debounce por alvo (evita rajada no streaming)
    var pending = false;
    return function () { if (pending) return; pending = true; requestAnimationFrame(function () { pending = false; fn(); }); };
  }

  // Limpa um nó SÓ se tiver emoji: troca por ícone SVG + texto, preservando
  // quebras de linha. Não toca em nós sem emoji (saudação/botões ficam intactos).
  function cleanNode(el, forceIcon) {
    if (!el || !HAS.test(el.textContent || "")) return;
    var ic = forceIcon || iconFor(el.textContent || "");
    var t = strip(el.textContent || "");
    el.style.whiteSpace = "pre-wrap";
    el.innerHTML = (ic ? '<span class="lead">' + svg(ic) + " Colônia</span>\n" : "") + esc(t);
  }

  function observe(el, fn) {
    if (!el) return;
    var run = debounced(fn);
    new MutationObserver(run).observe(el, { childList: true, subtree: true, characterData: true });
    run();
  }

  // Melhoria segura: liga os chips da saudação (data-fill) — antes eram
  // botões sem função. Clicar preenche o objetivo e envia à colônia (real).
  function wireQuickChips() {
    document.addEventListener("click", function (e) {
      var btn = e.target.closest && e.target.closest("[data-fill]");
      if (!btn) return;
      var input = $("chat-input"), send = $("chat-send");
      if (input && send) { input.value = btn.getAttribute("data-fill"); send.click(); }
    });
  }

  function init() {
    wireQuickChips();
    // 1) Mensagens do chat (só as que têm emoji; saudação com botões intacta).
    var msgs = $("messages");
    if (msgs) observe(msgs, function () { msgs.querySelectorAll(".msg").forEach(function (m) { cleanNode(m); }); });
    // 2) Cards de bot (🤖 → ícone operária).
    var grid = $("bot-grid");
    if (grid) observe(grid, function () { grid.querySelectorAll(".bot-card .name").forEach(function (n) { cleanNode(n, "i-worker"); }); });
    // 3) Resultado da factory (✅/⚠️/⏳).
    var fac = $("fac-result");
    if (fac) observe(fac, function () { cleanNode(fac); });
    // 4) Toast (😴 e afins) — texto puro, sem ícone.
    var toast = $("toast");
    if (toast) observe(toast, function () { if (HAS.test(toast.textContent || "")) toast.textContent = strip(toast.textContent); });
    // Dispara os carregadores da aba ativa (Colônia é a inicial na 6.4).
    var act = document.querySelector(".nav-item.active");
    if (act && act.dataset.tab)
      document.dispatchEvent(new CustomEvent("ants:tab", { detail: act.dataset.tab }));
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
