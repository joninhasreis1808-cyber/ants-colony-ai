/* Ant's — lógica principal: navegação, conexão, tema, PWA. */
const Ant = {
  api: location.origin,
  online: false,

  init() {
    this.wireTabs();
    this.wireTheme();
    this.checkHealth();
    setInterval(() => this.checkHealth(), 15000);
    this.registerSW();
    window.addEventListener("online", () => this.setConn(true));
    window.addEventListener("offline", () => this.setConn(false));
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
    } catch {
      this.setConn(false);
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

