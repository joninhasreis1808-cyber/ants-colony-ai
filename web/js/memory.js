/* Ant's — memória: busca, listagem, força e ciclo de sono. */
const Memory = {
  init() {
    const s = document.getElementById("mem-search");
    const sleep = document.getElementById("mem-sleep");
    if (s) s.addEventListener("click", () => this.search());
    if (sleep) sleep.addEventListener("click", () => this.sleep());
  },

  async refresh() {
    try {
      const r = await fetch(`${Ant.api}/memory/health`);
      const h = await r.json();
      const c = h.counts || {};
      document.getElementById("mem-stats").innerHTML =
        `<span class="chip">total ${c.total ?? 0}</span>` +
        `<span class="chip">fortes ${c.strong ?? 0}</span>` +
        `<span class="chip">médias ${c.medium ?? 0}</span>` +
        `<span class="chip">fracas ${c.weak ?? 0}</span>`;
    } catch {
      Ant.toast("Memória indisponível");
    }
  },

  async search() {
    const q = document.getElementById("mem-query").value.trim();
    if (!q) return;
    try {
      const r = await fetch(`${Ant.api}/memory/recall`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, limit: 10 }),
      });
      const data = await r.json();
      this.renderList(data.memories || []);
    } catch {
      Ant.toast("Falha na busca");
    }
  },

  renderList(items) {
    const box = document.getElementById("mem-list");
    if (!items.length) {
      box.innerHTML = '<p class="muted">Nenhuma memória encontrada.</p>';
      return;
    }
    box.innerHTML = items
      .map((m) => {
        const pct = Math.round((m.strength || 0) * 100);
        return (
          `<div class="mem-item">${m.content}` +
          `<div class="bar"><span style="width:${pct}%"></span></div></div>`
        );
      })
      .join("");
  },

  async sleep() {
    Ant.toast("😴 Iniciando ciclo de sono...");
    try {
      const r = await fetch(`${Ant.api}/memory/sleep`, { method: "POST" });
      const rep = await r.json();
      const c = rep.counts || {};
      Ant.toast(
        `Sono: ${c.consolidated || 0} consolidadas, ${c.patterns || 0} padrões`
      );
      this.refresh();
    } catch {
      Ant.toast("Falha no ciclo de sono");
    }
  },
};

document.addEventListener("DOMContentLoaded", () => Memory.init());
