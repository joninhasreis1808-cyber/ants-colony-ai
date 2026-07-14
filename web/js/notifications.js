/* Ant's — notificações proativas (aditivo, não altera a lógica existente).
   Usa a Notification API do navegador, sempre com permissão do usuário e
   com um limite diário para não incomodar. */
const AntNotify = {
  MAX_PER_DAY: 3,

  async init() {
    // Não pede permissão de cara; só quando houver algo a notificar.
    this._count = this._today();
  },

  _today() {
    const key = "ant-notify-" + new Date().toDateString();
    return parseInt(localStorage.getItem(key) || "0", 10);
  },

  _bump() {
    const key = "ant-notify-" + new Date().toDateString();
    localStorage.setItem(key, String(this._today() + 1));
  },

  async ensurePermission() {
    if (!("Notification" in window)) return false;
    if (Notification.permission === "granted") return true;
    if (Notification.permission === "denied") return false;
    const p = await Notification.requestPermission();
    return p === "granted";
  },

  // tipos: suggestion, alert, completion, insight
  async send(type, title, body) {
    if (this._today() >= this.MAX_PER_DAY) return false;
    const ok = await this.ensurePermission();
    if (!ok) return false;
    const labels = {
      suggestion: "Sugestão", alert: "Alerta",
      completion: "Concluído", insight: "Descoberta",
    };
    const prefix = labels[type] || "Colônia";
    new Notification(`${prefix} · ${title}`, {
      body, tag: "ants-" + type, icon: "/assets/icons/icon-192.png",
    });
    this._bump();
    return true;
  },
};

if (typeof window !== "undefined") {
  window.AntNotify = AntNotify;
  document.addEventListener("DOMContentLoaded", () => AntNotify.init());
}
