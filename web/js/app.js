/* Ant's — lógica principal: navegação, conexão, tema, PWA. */
const Ant = {
  api: location.origin,
  online: false,

  _hzHealthy: 15000,   // ritmo estável quando a colônia responde
  _backoff: 0,         // reconexão com backoff exponencial quando offline

  init() {
    this.wireTabs();
    this.wireTheme();
    // Fonte ÚNICA de saúde (9.4 · T6): um só /health por ciclo, distribuído por
    // "ants:health". Pausa em segundo plano (document.hidden) e limpa no unload.
    // Agendamento ADAPTATIVO (9.18 · FASE 2): não é intervalo fixo — recua no
    // backoff quando o Render hiberna e volta ao ritmo ao despertar; a UI nunca
    // trava nem martela o servidor.
    this._scheduleHealth(0);
    document.addEventListener("visibilitychange", () => { if (!document.hidden) this._scheduleHealth(0); });
    window.addEventListener("beforeunload", () => clearTimeout(this._hz));
    this.registerSW();
    window.addEventListener("online", () => { this.setConn(true); this._scheduleHealth(0); });
    window.addEventListener("offline", () => this.setConn(false));
  },

  // Próxima checagem em `delay`ms. Em segundo plano, só reprograma (não consulta).
  _scheduleHealth(delay) {
    clearTimeout(this._hz);
    this._hz = setTimeout(() => {
      if (document.hidden) { this._scheduleHealth(this._hzHealthy); return; }
      this.checkHealth();
    }, Math.max(0, delay));
  },

  // Backoff exponencial (FASE 2): 2s → 4s → 8s → 16s → teto 30s. Determinístico.
  _nextBackoff() {
    this._backoff = Math.min(this._backoff ? this._backoff * 2 : 2000, 30000);
    return this._backoff;
  },

  wireTabs() {
    document.querySelectorAll(".nav-btn").forEach((btn) => {
      btn.addEventListener("click", () => this.showTab(btn.dataset.tab));
    });
  },

  showTab(name) {
    document.querySelectorAll(".tab").forEach((t) =>
      t.classList.toggle("active", t.id === `tab-${name}`)
    );
    document.querySelectorAll(".nav-btn").forEach((b) =>
      b.classList.toggle("active", b.dataset.tab === name)
    );
    if (name === "memory" && window.Memory) Memory.refresh();
    if (name === "settings") this.showHealth();
  },

  wireTheme() {
    const toggle = document.getElementById("theme-toggle");
    const saved = localStorage.getItem("ant-theme");
    if (saved === "light") { document.body.classList.add("light"); toggle.checked = true; }
    toggle.addEventListener("change", () => {
      document.body.classList.toggle("light", toggle.checked);
      localStorage.setItem("ant-theme", toggle.checked ? "light" : "dark");
    });
  },

  setConn(ok) {
    this.online = ok;
    const el = document.getElementById("conn");
    el.textContent = ok ? "online" : "offline";
    el.className = "conn " + (ok ? "online" : "offline");
  },

  async checkHealth() {
    try {
      const r = await fetch(`${this.api}/health`);
      this.setConn(r.ok);
      this._health = await r.json();
      // distribui a saúde a quem ouve (rodapé, painéis) — 1 requisição só.
      document.dispatchEvent(new CustomEvent("ants:health", { detail: this._health }));
      this._backoff = 0;                       // saudável → zera o backoff
      this._scheduleHealth(this._hzHealthy);   // volta ao ritmo estável
    } catch {
      this.setConn(false);
      document.dispatchEvent(new CustomEvent("ants:health", { detail: null }));
      // Reconexão com backoff exponencial (FASE 2): sonda o despertar da colônia
      // (Render hiberna no free tier) sem travar a UI nem martelar o servidor.
      this._scheduleHealth(this._nextBackoff());
    }
  },

  showHealth() {
    const box = document.getElementById("health-info");
    if (!box || !this._health) return;
    const h = this._health;
    box.innerHTML =
      `<span class="chip">versão ${h.version}</span>` +
      `<span class="chip">${h.bots_active} bots</span>` +
      `<span class="chip">${h.memories_stored} memórias</span>` +
      `<span class="chip">uptime ${Math.round(h.uptime_seconds)}s</span>`;
  },

  toast(msg) {
    const t = document.getElementById("toast");
    t.textContent = msg;
    t.classList.add("show");
    setTimeout(() => t.classList.remove("show"), 2500);
  },

  registerSW() {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    }
  },
};

document.addEventListener("DOMContentLoaded", () => Ant.init());

/* ── Realce visual (aditivo, sem lógica de negócio) ──
   Reaplica uma animação de entrada ao trocar de aba, dando a sensação
   orgânica de "foco" da colmeia. Não altera navegação nem dados: apenas
   observa mudanças de classe nas seções .tab e dispara a animação CSS. */
document.addEventListener("DOMContentLoaded", () => {
  const tabs = document.querySelectorAll(".tab");
  const replay = (el) => {
    el.style.animation = "none";
    void el.offsetWidth; // força reflow para reiniciar a animação
    el.style.animation = "";
  };
  tabs.forEach((tab) => {
    new MutationObserver(() => {
      if (tab.classList.contains("active")) replay(tab);
    }).observe(tab, { attributes: true, attributeFilter: ["class"] });
  });
});

