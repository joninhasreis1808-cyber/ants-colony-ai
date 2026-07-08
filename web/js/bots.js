/* Ant's — dashboard de bots: cards de status e log em tempo real. */
const Bots = {
  roster: ["navigator", "extractor", "interpreter", "decider", "learner"],

  init() {
    this.render();
    const send = document.getElementById("task-send");
    if (send) send.addEventListener("click", () => this.newTask());
  },

  render() {
    const grid = document.getElementById("bot-grid");
    if (!grid) return;
    grid.innerHTML = this.roster
      .map(
        (name) =>
          `<div class="bot-card" id="bot-${name}">` +
          `<div class="name">🤖 ${name}</div>` +
          `<div class="state">idle</div></div>`
      )
      .join("");
  },

  setState(name, state) {
    const card = document.getElementById(`bot-${name}`);
    if (!card) return;
    card.className = `bot-card ${state}`;
    card.querySelector(".state").textContent = state;
  },

  logLine(text) {
    const log = document.getElementById("bot-log");
    if (!log) return;
    const div = document.createElement("div");
    div.textContent = text;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
  },

  async newTask() {
    const input = document.getElementById("task-input");
    const goal = input.value.trim();
    if (!goal) return;
    input.value = "";
    this.roster.forEach((b) => this.setState(b, "idle"));
    this.logLine(`▶ Nova tarefa: ${goal}`);
    try {
      const r = await fetch(`${Ant.api}/hive/task`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal }),
      });
      const { task_id } = await r.json();
      this.watch(task_id);
    } catch {
      Ant.toast("Colmeia indisponível");
    }
  },

  watch(taskId) {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${location.host}/hive/live/${taskId}`);
    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      if (data.type === "end") {
        this.roster.forEach((b) => this.setState(b, "done"));
        this.logLine("■ Tarefa concluída");
        ws.close();
        return;
      }
      const e = data.event;
      if (this.roster.includes(e.bot)) this.setState(e.bot, "working");
      this.logLine(`${e.bot} [${e.phase}]: ${e.message}`);
    };
  },
};

document.addEventListener("DOMContentLoaded", () => Bots.init());
