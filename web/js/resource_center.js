/* Ant's — resource_center.js: monitoramento de recursos em tempo real.
   Visual e aditivo. Mostra CPU/RAM/disco/rede/bateria com cores de status.
   Alimenta-se de valores injetados ou de uma demonstração animada. */
(function () {
  "use strict";
  const METRICS = [
    { key: "cpu",     label: "CPU" },
    { key: "ram",     label: "RAM" },
    { key: "disk",    label: "Disco" },
    { key: "net",     label: "Rede" },
    { key: "battery", label: "Bateria" },
  ];
  function color(v, inverted) {
    const x = inverted ? 100 - v : v;
    if (x > 75) return "var(--ant-ember)";
    if (x > 45) return "var(--ant-amber)";
    return "var(--ant-leaf)";
  }
  function render(el, values) {
    el.innerHTML = "";
    values = values || {};
    METRICS.forEach((m) => {
      // Sem valor real => "—" e barra vazia. Nunca inventar (sem Math.random).
      const has = values[m.key] != null;
      const v = has ? values[m.key] : 0;
      const inv = m.key === "battery";
      const row = document.createElement("div");
      row.style.cssText = "margin-bottom:8px";
      row.innerHTML =
        '<div style="display:flex;justify-content:space-between;font-size:12px;' +
        'color:var(--ant-text-secondary);margin-bottom:3px"><span>' + m.label +
        '</span><span>' + (has ? v + '%' : '—') + '</span></div>' +
        '<div style="height:7px;background:var(--ant-bg-deep);border-radius:5px;overflow:hidden">' +
        '<div style="height:100%;width:' + v + '%;border-radius:5px;background:' +
        color(v, inv) + '"></div></div>';
      el.appendChild(row);
    });
  }
  function mount(id, values) {
    const el = document.getElementById(id);
    if (el) render(el, values || {});
  }
  window.AntResources = { mount, render };
})();
