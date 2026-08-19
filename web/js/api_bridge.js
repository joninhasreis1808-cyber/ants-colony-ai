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
    if (track && method === "POST" && /\/hive\/task\b/.test(url)) {
      captureGoal(init);
      // "Buscar de novo" (9.4 · T3): injeta fresh:true no corpo p/ ignorar o
      // cache, sem tocar no chat.js legado. A flag é armada pelo selo.
      if (window.__antFresh) { init = withFresh(init); window.__antFresh = false; }
    }
    try {
      const res = await orig(input, init);
      if (track) { logCall(method, url.replace(api, "") || url, res.status, Math.round(performance.now() - t0)); AntAPI._mark(res.ok); }
      if (track && method === "POST" && /\/hive\/task\b/.test(url))
        res.clone().json().then((d) => {
          const id = d && (d.task_id || d.id);
          if (id) startFlow(id, d && d.echo);  // eco imediato (§4.2)
        }).catch(() => {});
      return res;
    } catch (e) {
      if (track) { logCall(method, url.replace(api, "") || url, "ERRO", Math.round(performance.now() - t0)); AntAPI._mark(false); }
      throw e;
    }
  };

  function captureGoal(init) {
    try { const b = JSON.parse((init && init.body) || "{}"); if (b.goal) window.__antLastQuestion = b.goal; } catch (e) {}
  }

  function withFresh(init) {
    try {
      const b = JSON.parse((init && init.body) || "{}"); b.fresh = true;
      return Object.assign({}, init, { body: JSON.stringify(b) });
    } catch (e) { return init; }
  }

  // Progresso dirigido por EVENTOS REAIS (9.2 · Bloco C): a fase do último
  // evento do backend (plan→do→check→act) mapeia para a etapa do fluxo. Nada
  // de contador por tempo — o % reflete o andamento verdadeiro.
  const ORDER = ["plan", "do", "check", "act"];
  const FLOOR = { plan: 2, do: 4, check: 6, act: 7 };
  function stepFromEvents(evs, lastStep) {
    if (!evs || !evs.length) return 1;                 // Rainha recebeu
    const last = evs[evs.length - 1];
    const base = FLOOR[last.phase];
    if (base == null) return lastStep;
    const idx = ORDER.indexOf(last.phase);
    const nextFloor = idx < ORDER.length - 1 ? FLOOR[ORDER[idx + 1]] : 8;
    const same = evs.filter((e) => e.phase === last.phase).length;
    return Math.min(base + Math.max(0, same - 1), nextFloor - 1);
  }

  // Transporte de eventos (9.4 · T5): WebSocket /hive/live/{id} é o PRIMÁRIO;
  // o polling de /hive/status vira FALLBACK automático (o serviço hiberna no
  // free tier). Antes: ~100 req/min por aba. Agora: ~2 fetches por missão
  // (backfill na abertura + status final). O formato de ants:task-tick é o
  // MESMO — a Câmera ao Vivo e a barra de progresso não mudam.
  function startFlow(taskId, echo) {
    const flow = document.getElementById("research-flow");
    if (!flow) return;
    flow.classList.add("show");
    const steps = [].slice.call(flow.querySelectorAll(".flow-step"));
    const arms = [].slice.call(flow.querySelectorAll(".flow-arm"));
    const last = steps.length - 1;
    const pct = document.getElementById("flow-pct"), narr = document.getElementById("flow-narr");
    const esc = (s) => String(s == null ? "" : s).replace(/[&<>]/g,
      (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
    if (narr && echo) narr.innerHTML = "<b>" + esc(echo) + "</b>";
    let i = 0, finished = false;
    const paint = () => {
      steps.forEach((s, k) => { s.classList.toggle("on", k === i); s.classList.toggle("done", k < i); });
      arms.forEach((a, k) => a.classList.toggle("lit", k < i));
      if (pct) pct.textContent = Math.round(i / last * 100) + "%";
    };
    paint();
    const isDone = (st) => st && ["done", "completed", "failed"].includes(st.status);

    // Renderiza e dispara ants:task-tick a partir de um status (fonte única).
    const emit = (st, done) => {
      st = st || {};
      if (narr) {
        const r = st.result || {};
        if (done) {
          var motivo = [];
          if (r.confidence != null) motivo.push("confiança " + r.confidence);
          var nsrc = (r.sources || []).length;
          motivo.push(nsrc + (nsrc === 1 ? " fonte externa" : " fontes externas"));
          if (r.cognition && r.cognition.knowledge_used != null)
            motivo.push(r.cognition.knowledge_used + " fatos da memória");
          narr.innerHTML = "<b>" + esc(r.answer ? "Resposta pronta." : "Concluído.") +
            "</b>" + (motivo.length ? ' <span style="color:var(--dim)">· ' + esc(motivo.join(" · ")) + "</span>" : "");
        } else {
          const evs = st.events || [];
          const ev = evs.length ? evs[evs.length - 1] : null;
          narr.innerHTML = ev ? "<b>" + esc(ev.bot) + "</b> · " + esc(ev.message)
            : "a colônia trabalha…";
        }
      }
      const target = done ? last : stepFromEvents(st.events, i);
      if (target > i) i = target;
      paint();
      document.dispatchEvent(new CustomEvent("ants:task-tick", {
        detail: { taskId: taskId, pct: Math.round(i / last * 100), done: !!done, status: st },
      }));
      if (done) document.dispatchEvent(new CustomEvent("ants:task-done", { detail: st }));
    };

    const finish = async (st) => {
      if (finished) return; finished = true;
      if (!st || !st.result) { try { st = await AntAPI.get("/hive/status/" + taskId); } catch (e) {} }
      emit(st, true);
    };

    // Fallback: polling de /hive/status a cada 600ms (só se o WS falhar).
    let poll = null;
    const startPolling = () => {
      if (poll || finished) return;
      const tick = async () => {
        let st = null; try { st = await AntAPI.get("/hive/status/" + taskId); } catch (e) {}
        if (isDone(st)) { clearInterval(poll); poll = null; finish(st); return; }
        emit(st, false);
      };
      tick(); poll = setInterval(tick, 600);
      setTimeout(() => { if (poll) { clearInterval(poll); poll = null; } }, 30000);
    };

    // Primário: WebSocket.
    let ws = null;
    try {
      const proto = location.protocol === "https:" ? "wss:" : "ws:";
      ws = new WebSocket(proto + "//" + location.host + "/hive/live/" + taskId);
    } catch (e) { ws = null; }
    if (!ws) { startPolling(); return; }

    const events = [], seen = {};
    let opened = false, gotEnd = false;
    const push = (ev) => {
      const id = ev && (ev.id || (ev.bot + "|" + ev.phase + "|" + ev.ts));
      if (id && !seen[id]) { seen[id] = 1; events.push(ev); }
    };
    const failTimer = setTimeout(() => {
      if (!opened) { try { ws.close(); } catch (e) {} startPolling(); }
    }, 1800);
    ws.onopen = async () => {
      opened = true; clearTimeout(failTimer);
      // Backfill: eventos já emitidos antes do WS assinar (não perde bots).
      try {
        const st0 = await AntAPI.get("/hive/status/" + taskId);
        (st0.events || []).forEach(push);
        if (isDone(st0)) { gotEnd = true; try { ws.close(); } catch (e) {} return finish(st0); }
        emit({ status: "running", events: events, result: null }, false);
      } catch (e) {}
    };
    ws.onmessage = (m) => {
      let d; try { d = JSON.parse(m.data); } catch (e) { return; }
      if (d.type === "event" && d.event) { push(d.event); emit({ status: "running", events: events, result: null }, false); }
      else if (d.type === "end") { gotEnd = true; try { ws.close(); } catch (e) {} finish(); }
    };
    ws.onerror = () => {};
    ws.onclose = () => { clearTimeout(failTimer); if (!gotEnd && !finished) startPolling(); };
    setTimeout(() => { if (!finished) { try { ws.close(); } catch (e) {} finish(); } }, 45000);
  }
})();
