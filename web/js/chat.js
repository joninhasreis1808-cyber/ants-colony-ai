/* Ant's — chat: envia tarefa à colmeia e transmite eventos em tempo real. */
const Chat = {
  init() {
    const send = document.getElementById("chat-send");
    const input = document.getElementById("chat-input");
    send.addEventListener("click", () => this.send());
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") this.send();
    });
    this.load();
  },

  add(text, who) {
    const box = document.getElementById("messages");
    const div = document.createElement("div");
    div.className = `msg ${who}`;
    div.textContent = text;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    this.history.push({ text, who });
    localStorage.setItem("ant-chat", JSON.stringify(this.history.slice(-50)));
    return div;
  },

  load() {
    this.history = JSON.parse(localStorage.getItem("ant-chat") || "[]");
    const box = document.getElementById("messages");
    this.history.forEach(({ text, who }) => {
      const div = document.createElement("div");
      div.className = `msg ${who}`;
      div.textContent = text;
      box.appendChild(div);
    });
  },

  async send() {
    const input = document.getElementById("chat-input");
    const goal = input.value.trim();
    if (!goal) return;
    this.add(goal, "user");
    input.value = "";
    const status = this.add("🐜 A colmeia está trabalhando...", "bot");
    try {
      const r = await fetch(`${Ant.api}/hive/task`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal }),
      });
      const { task_id } = await r.json();
      this.stream(task_id, status);
    } catch {
      status.textContent = "⚠️ Não consegui contatar a colmeia (offline?).";
    }
  },

  stream(taskId, statusEl) {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${location.host}/hive/live/${taskId}`);
    const lines = [];
    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      if (data.type === "end") {
        this.finish(taskId, statusEl);
        ws.close();
        return;
      }
      const e = data.event;
      lines.push(`${e.bot}: ${e.message}`);
      statusEl.textContent = lines.slice(-6).join("\n");
    };
    ws.onerror = () => { statusEl.textContent = "⚠️ Conexão interrompida."; };
  },

  async finish(taskId, statusEl) {
    try {
      const r = await fetch(`${Ant.api}/hive/status/${taskId}`);
      const task = await r.json();
      const res = task.result || {};
      statusEl.textContent = res.answer
        ? `✅ ${res.answer}\n(confiança: ${res.confidence ?? "?"})`
        : "✅ Tarefa concluída.";
    } catch {
      statusEl.textContent = "✅ Tarefa concluída.";
    }
  },
};

document.addEventListener("DOMContentLoaded", () => Chat.init());
