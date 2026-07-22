/* Ant's — timeline.js: linha do tempo das decisões da colônia.
   Visual e aditivo. Cada entrada mostra horário, ação, casta responsável. */
(function () {
  "use strict";
  function render(el, entries) {
    el.innerHTML = "";
    // Sem eventos reais => estado adormecido. Nunca usar dados de exemplo.
    if (!entries || !entries.length) {
      el.innerHTML = '<div style="color:var(--ant-text-secondary);font-family:var(--mono);' +
        'font-size:12px;padding:10px">Colônia adormecida — sem eventos ainda.</div>';
      return;
    }
    entries.forEach((e) => {
      const row = document.createElement("div");
      row.className = e.caste;
      row.style.cssText = "display:flex;align-items:center;gap:10px;padding:9px 12px;" +
        "border-left:2px solid var(--caste);margin-bottom:5px;background:var(--ant-bg-surface);" +
        "border-radius:0 8px 8px 0";
      row.innerHTML =
        '<span style="font-size:11px;color:var(--ant-text-secondary);min-width:42px">' + e.t + '</span>' +
        '<svg class="ico ico-sm" style="color:var(--caste)"><use href="#' + e.ico + '"/></svg>' +
        '<span style="font-size:13px">' + e.txt + '</span>';
      el.appendChild(row);
    });
  }
  function mount(id, entries) {
    const el = document.getElementById(id);
    if (el) render(el, entries);
  }
  window.AntTimeline = { mount, render };
})();
