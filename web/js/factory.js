/* Ant's — factory: cria apps a partir de descrição em linguagem natural. */
const Factory = {
  steps: [
    "Analisando requisitos", "Projetando arquitetura", "Selecionando template",
    "Gerando código", "Testando", "Documentando", "Finalizando",
  ],

  init() {
    const btn = document.getElementById("fac-create");
    if (btn) btn.addEventListener("click", () => this.create());
  },

  async create() {
    const desc = document.getElementById("fac-desc").value.trim();
    const template = document.getElementById("fac-template").value;
    if (!desc && !template) {
      Ant.toast("Descreva o app ou escolha um template");
      return;
    }
    const out = document.getElementById("fac-result");
    out.textContent = "";
    this.animateSteps(out);
    try {
      const endpoint = template
        ? `${Ant.api}/factory/quick`
        : `${Ant.api}/factory/create`;
      const body = template
        ? { description: `${template}: ${desc || template}` }
        : { description: desc, options: { run_tests: true } };
      const r = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await r.json();
      clearInterval(this._timer);
      this.showResult(out, data);
    } catch {
      clearInterval(this._timer);
      out.textContent = "⚠️ Não consegui criar o app (backend offline?).";
    }
  },

  animateSteps(out) {
    let i = 0;
    this._timer = setInterval(() => {
      if (i < this.steps.length) {
        out.textContent = `⏳ ${this.steps[i]}...`;
        i++;
      }
    }, 400);
  },

  showResult(out, data) {
    const s = data.summary || data;
    const sugg = (data.suggestions || [])
      .map((x) => `\n  • ${x}`)
      .join("");
    out.textContent =
      `✅ App criado!\n\n` +
      `Tipo: ${s.type}\n` +
      `Arquivos: ${s.files}\n` +
      `Testes: ${s.tests}\n` +
      `Linhas: ${s.lines}\n` +
      `Testado: ${s.tested === true ? "sim ✅" : s.tested === false ? "não" : "—"}\n` +
      (s.deployed ? `Deploy: ${s.deployed}\n` : "") +
      (sugg ? `\nSugestões:${sugg}` : "");
    Ant.toast("App criado com sucesso!");
  },
};

document.addEventListener("DOMContentLoaded", () => Factory.init());
