/* Ant's — live_dashboard.js: visão organizacional (hierarquia) + biológica
   (rede viva) da colônia. Puramente visual e aditivo. Renderiza os bots por
   casta e desenha uma rede SVG simples com nós e conexões que pulsam. */
(function () {
  "use strict";
  const COLONY = [
    { caste: "queen",    label: "Rainha",       cls: "caste-queen",    icon: "i-crown",  active: 1, total: 1 },
    { caste: "explorer", label: "Exploradoras", cls: "caste-explorer", icon: "i-compass",active: 3, total: 5 },
    { caste: "worker",   label: "Operárias",    cls: "caste-worker",   icon: "i-worker", active: 5, total: 6 },
    { caste: "gardener", label: "Jardineiras",  cls: "caste-gardener", icon: "i-leaf",   active: 2, total: 2 },
    { caste: "soldier",  label: "Soldados",     cls: "caste-soldier",  icon: "i-shield", active: 2, total: 2 },
    { caste: "nurse",    label: "Cuidadoras",   cls: "caste-nurse",    icon: "i-nurse",  active: 1, total: 2 },
  ];

  function renderHierarchy(el) {
    el.innerHTML = "";
    COLONY.forEach((c) => {
      const row = document.createElement("div");
      row.className = "org-row " + c.cls;
      row.style.cssText = "display:flex;align-items:center;gap:10px;padding:9px 12px;" +
        "border-left:3px solid var(--caste);background:var(--ant-bg-surface);" +
        "border-radius:8px;margin-bottom:6px";
      row.innerHTML =
        '<svg class="ico" style="color:var(--caste)"><use href="#' + c.icon + '"/></svg>' +
        '<span style="font-weight:600">' + c.label + '</span>' +
        '<span style="margin-left:auto;font-size:12px;color:var(--ant-text-secondary)">' +
        c.active + "/" + c.total + " ativas</span>";
      el.appendChild(row);
    });
  }

  function renderNetwork(el) {
    const W = el.clientWidth || 320, H = 240, cx = W / 2, cy = H / 2;
    const svg = ['<svg viewBox="0 0 ' + W + ' ' + H + '" style="width:100%;height:240px">'];
    const pts = COLONY.map((c, i) => {
      const ang = (i / COLONY.length) * Math.PI * 2 - Math.PI / 2;
      const r = c.caste === "queen" ? 0 : 88;
      return { x: cx + Math.cos(ang) * r, y: cy + Math.sin(ang) * r, c: c };
    });
    // conexões da rainha (centro) a cada casta
    pts.forEach((p, i) => {
      if (i === 0) return;
      const t = p.c.active > 0 ? " transmitting" : "";
      svg.push('<line class="colony-link' + t + '" x1="' + pts[0].x + '" y1="' +
        pts[0].y + '" x2="' + p.x + '" y2="' + p.y + '"/>');
    });
    pts.forEach((p) => {
      const st = p.c.active === 0 ? " idle" : (p.c.active < p.c.total ? " busy" : "");
      const rad = 12 + p.c.active * 2;
      svg.push('<circle class="colony-node ' + p.c.cls + st + '" cx="' + p.x +
        '" cy="' + p.y + '" r="' + rad + '"/>');
    });
    svg.push("</svg>");
    el.innerHTML = svg.join("");
  }

  function mount(hierId, netId) {
    const h = document.getElementById(hierId), n = document.getElementById(netId);
    if (h) renderHierarchy(h);
    if (n) renderNetwork(n);
  }
  window.AntDashboard = { mount, COLONY };
})();
