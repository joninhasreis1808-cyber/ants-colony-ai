/* Ant's — cognitive_center.js: o "cérebro" da colônia em tempo real.
   Mostra as 9 camadas cognitivas com barras de ativação. Puramente visual
   e aditivo — anima valores de demonstração ou os que forem injetados. */
(function () {
  "use strict";
  const LAYERS = [
    { key: "planner",     name: "Planejamento", caste: "caste-queen" },
    { key: "researcher",  name: "Pesquisa",     caste: "caste-explorer" },
    { key: "hypothesizer",name: "Hipóteses",    caste: "caste-explorer" },
    { key: "inference",   name: "Inferência",   caste: "caste-worker" },
    { key: "simulator",   name: "Simulação",    caste: "caste-gardener" },
    { key: "critic",      name: "Crítica",      caste: "caste-soldier" },
    { key: "verifier",    name: "Verificação",  caste: "caste-soldier" },
    { key: "learner",     name: "Aprendizado",  caste: "caste-nurse" },
    { key: "executor",    name: "Execução",     caste: "caste-worker" },
  ];

  function render(container) {
    container.innerHTML = "";
    LAYERS.forEach((l) => {
      const row = document.createElement("div");
      row.className = "cog-layer " + l.caste;
      row.innerHTML =
        '<div class="cog-name"><span>' + l.name + '</span>' +
        '<span id="cog-pct-' + l.key + '">0%</span></div>' +
        '<div class="cog-track"><div class="cog-fill" id="cog-fill-' +
        l.key + '"></div></div>';
      container.appendChild(row);
    });
  }

  function setActivation(values) {
    LAYERS.forEach((l) => {
      const v = Math.max(0, Math.min(100, values[l.key] != null
        ? values[l.key] : Math.round(40 + Math.random() * 60)));
      const fill = document.getElementById("cog-fill-" + l.key);
      const pct = document.getElementById("cog-pct-" + l.key);
      if (fill) fill.style.width = v + "%";
      if (pct) pct.textContent = v + "%";
    });
  }

  function mount(targetId) {
    const el = document.getElementById(targetId);
    if (!el) return;
    render(el);
    setActivation({});
  }

  window.AntCognitive = { mount, setActivation, LAYERS };
})();
