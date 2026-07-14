/* Ant's — permissões de dispositivo (aditivo).
   Solicita cada permissão NO MOMENTO DO USO, explicando o quê e por quê.
   Revogável a qualquer momento. Nunca acessa sem consentimento. */
const AntPermissions = {
  _granted: {},

  labels: {
    notifications: "enviar alertas úteis",
    clipboard: "ler/escrever a área de transferência",
    geolocation: "usar sua localização",
    microphone: "ouvir sua voz",
    camera: "capturar imagens",
  },

  async request(kind) {
    const why = this.labels[kind] || kind;
    // Confirmação explícita antes de acionar a API do navegador.
    if (!window.confirm(`A colônia quer ${why}. Permitir agora?`)) {
      this._granted[kind] = false;
      return false;
    }
    let ok = false;
    try {
      if (kind === "notifications" && "Notification" in window) {
        ok = (await Notification.requestPermission()) === "granted";
      } else if (kind === "geolocation" && navigator.geolocation) {
        ok = await new Promise((res) =>
          navigator.geolocation.getCurrentPosition(() => res(true), () => res(false))
        );
      } else if (kind === "microphone" || kind === "camera") {
        const c = kind === "microphone" ? { audio: true } : { video: true };
        const s = await navigator.mediaDevices.getUserMedia(c);
        s.getTracks().forEach((t) => t.stop());
        ok = true;
      } else if (kind === "clipboard") {
        ok = true; // uso real acontece sob gesto do usuário
      }
    } catch {
      ok = false;
    }
    this._granted[kind] = ok;
    this._render();
    return ok;
  },

  revoke(kind) {
    this._granted[kind] = false;
    this._render();
  },

  active() {
    return Object.entries(this._granted)
      .filter(([, v]) => v)
      .map(([k]) => k);
  },

  _render() {
    const box = document.getElementById("perm-indicator");
    if (!box) return;
    const active = this.active();
    box.innerHTML = active.length
      ? active.map((k) => `<span class="chip"><svg class="ico ico-sm"><use href="#i-shield"/></svg> ${k}</span>`).join("")
      : '<span class="muted">Nenhuma permissão ativa</span>';
  },
};

if (typeof window !== "undefined") window.AntPermissions = AntPermissions;
