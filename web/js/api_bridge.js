/* Ant's — api_bridge.js: ponte real com a API.
   1) Intercepta window.fetch e registra CADA chamada à API no console do
      navegador (prova de que a interface fala com o backend).
   2) Detecta online/adormecida e expõe AntAPI.get/post.
   3) Ao ver POST /hive/task, captura o task_id e anima o "Fluxo da colônia"
      lendo /hive/status/{id} de verdade. Sem dados falsos. */
(function () {
  "use strict";
  const api = location.origin;
  const orig = window.fetch.bind(window);
  const API_RE = /\/(health|hive|mind|colony|organism|bio|memory|factory|events|metrics|perceive|permissions|action)\b/;

  const AntAPI = {
    online: null,
    async get(p) { const r = await orig(api + p, { cache: "no-store" }); if (!r.ok) throw new Error(r.status); return r.json(); },
    async post(p, body) {
      const r = await orig(api + p, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
      if (!r.ok) throw new Error(r.status); return r.json();
    },
    _mark(ok) { if (ok !== this.online) { this.online = ok; document.dispatchEvent(new CustomEvent("ants:online", { detail: ok })); } },
  };
  window.AntAPI = AntAPI;

  function logCall(method, path, status, ms) {
    console.info("%c[Ant's → API]", "color:#d4a017;font-weight:bold",
      method, path, "→", status, ms + "ms");
    document.dispatchEvent(new CustomEvent("ants:netcall", { detail: { method, path, status, ms } }));
  }

  window.fetch = async function (input, init) {
    const url = typeof input === "string" ? input : (input && input.url) || "";
    const method = ((init && init.method) || (input && input.method) || "GET").toUpperCase();
    const t0 = performance.now();
    const track = API_RE.test(url);
    if (track && method === "POST" && /\/hive\/task\b/.test(url)) captureGoal(init);
    try {
      const res = await orig(input, init);
      if (track) { logCall(method, url.replace(api, "") || url, res.status, Math.round(performance.now() - t0)); AntAPI._mark(res.ok); }
      if (track && method === "POST" && /\/hive\/task\b/.test(url))
        res.clone().json().then((d) => { const id = d && (d.task_id || d.id); if (id) startFlow(id); }).catch(() => {});
      return res;
    } catch (e) {
      if (track) { logCall(method, url.replace(api, "") || url, "ERRO", Math.round(performance.now() - t0)); AntAPI._mark(false); }
      throw e;
    }
  };

  function captureGoal(init) {
    try { const b = JSON.parse((init && init.body) || "{}"); if (b.goal) window.__antLastQuestion = b.goal; } catch (e) {}
  }

  function startFlow(taskId) {
    const flow = document.getElementById("research-flow");
    if (!flow) return;
    flow.classList.add("show");
    const steps = [].slice.call(flow.querySelectorAll(".flow-step"));
    const arms = [].slice.call(flow.querySelectorAll(".flow-arm"));
    const pct = document.getElementById("flow-pct"), narr = document.getElementById("flow-narr");
    let i = 0;
    const paint = () => {
      steps.forEach((s, k) => { s.classList.toggle("on", k === i); s.classList.toggle("done", k < i); });
      arms.forEach((a, k) => a.classList.toggle("lit", k < i));
      if (pct) pct.textContent = Math.round(i / (steps.length - 1) * 100) + "%";
    };
    paint();
    const poll = setInterval(async () => {
      let st = null;
      try { st = await AntAPI.get("/hive/status/" + taskId); } catch (e) {}
      const done = st && ["done", "completed", "failed"].includes(st.status);
      if (st && narr) { const r = st.result || {}; narr.innerHTML = done ? "<b>" + (r.answer ? "Resposta pronta." : "Concluído.") + "</b>" : "a colônia trabalha…"; }
      if (done) { i = steps.length - 1; paint(); if (pct) pct.textContent = "100%"; clearInterval(poll); document.dispatchEvent(new CustomEvent("ants:task-done")); return; }
      if (i < steps.length - 2) i++;
      paint();
    }, 600);
    setTimeout(() => clearInterval(poll), 30000);
  }
})();
