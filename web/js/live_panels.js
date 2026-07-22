/* Ant's — live_panels.js: cada painel lê o endpoint REAL. Sem mockup.
   Falha de endpoint => "colônia adormecida" (nunca números falsos). */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const set = (id, v) => { const e = $(id); if (e) e.textContent = v == null ? "—" : v; };
  const cap = (s) => (s || "").charAt(0).toUpperCase() + (s || "").slice(1);
  const esc = (s) => String(s).replace(/[<>&]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;" }[c]));
  const dorm = '<div class="mono" style="color:var(--dim);font-size:12px">Colônia adormecida.</div>';
  const A = () => window.AntAPI;

  function bar(label, v) {
    const has = v != null && !isNaN(v);
    return '<div style="margin-bottom:8px"><div style="display:flex;justify-content:space-between;' +
      'font-size:12px;color:var(--muted)"><span>' + esc(label) + "</span><span>" +
      (has ? Math.round(v) + "%" : "—") + '</span></div><div style="height:7px;background:var(--bg2);' +
      'border-radius:5px;overflow:hidden"><div style="height:100%;width:' + (has ? Math.max(0, Math.min(100, v)) : 0) +
      '%;background:var(--amber)"></div></div></div>';
  }

  function setDormant() {
    const app = $("app"); if (app) app.setAttribute("data-colony-state", "dormant");
    if ($("state-ind")) $("state-ind").textContent = "Adormecida";
    const ci = $("connection-indicator"); if (ci) { ci.textContent = "Adormecida"; ci.classList.add("offline"); }
    ["stat-bots", "stat-tasks", "stat-uptime", "nav-bot-count", "env-reqs", "env-nodes",
     "memory-strength", "env-files", "env-procs", "env-domains", "env-verified",
     "env-relations", "env-confidence", "env-mem-short", "env-mem-consolidated"].forEach((id) => set(id, "—"));
    ["missions-list", "queen-decisions", "resource-center", "network-center", "cognition-hypotheses"].forEach((id) => { if ($(id)) $(id).innerHTML = dorm; });
    if ($("console-log")) $("console-log").innerHTML = '<div class="ln warn"><span class="lc">OFFLINE</span><span class="lm">colônia adormecida — sem backend</span></div>';
    if (window.AntTimeline) AntTimeline.mount("decision-timeline", null);
    if (window.AntCognitive) AntCognitive.setActivation({});
  }

  async function boot() {
    try { const h = await A().get("/health"); onHealth(h); return true; }
    catch (e) { setDormant(); return false; }
  }

  function onHealth(h) {
    const ci = $("connection-indicator"); if (ci) { ci.textContent = "Conectado"; ci.classList.remove("offline"); }
    set("stat-bots", h.bots_active); set("stat-tasks", h.tasks_submitted); set("nav-bot-count", h.bots_active);
    const s = Math.floor(h.uptime_seconds || 0);
    set("stat-uptime", String((s / 60) | 0).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0"));
  }

  async function fillResources() {
    if (!(await boot())) return;
    const rc = $("resource-center");
    try {
      const v = await A().get("/organism/vitals"); const H = v.hormones || {};
      if (rc) rc.innerHTML = Object.keys(H).map((k) => bar(cap(k), (H[k] || 0) * 100)).join("") +
        '<div class="mono" style="font-size:11px;color:var(--dim);margin-top:6px">apetite a risco ' +
        (v.risk_appetite ?? "—") + " · fase " + (v.circadian_phase || "—") + " · imunidade " + (v.immune_signatures ?? 0) + "</div>";
    } catch (e) { if (rc) rc.innerHTML = dorm; }
    const nc = $("network-center");
    try {
      const su = await A().get("/events/summary");
      set("env-reqs", (su.by_type || {}).ACTION_STARTED || 0);
      if (nc) nc.innerHTML = Object.entries(su.by_type || {}).map(([k, n]) => bar(k, Math.min(100, n * 4))).join("") || dorm;
    } catch (e) { if (nc) nc.innerHTML = dorm; }
    try { const st = await A().get("/colony/state"); setState(st.state); } catch (e) {}
    try { const m = await A().get("/memory/health"); set("env-mem-short", m.short_term ?? m.count ?? "—"); set("memory-strength", m.avg_strength ?? "—"); } catch (e) {}
  }

  const STATE_PT = {
    dormant: "Adormecida", observing: "Observando", exploring: "Explorando",
    building: "Construindo", learning: "Aprendendo", defending: "Defendendo",
    executing: "Executando", verifying: "Verificando", emergency: "Emergência",
  };
  function setState(s) {
    if (!s) return;
    const app = $("app"); if (app) app.setAttribute("data-colony-state", s);
    if ($("state-ind")) $("state-ind").textContent = STATE_PT[s] || cap(s);
  }

  async function fillCognition() {
    const q = window.__antLastQuestion, th = $("cognition-thought"), hyp = $("cognition-hypotheses");
    if (!q) { if (th) th.textContent = "Aguardando um objetivo — envie uma pergunta no Chat."; if (window.AntCognitive) AntCognitive.setActivation({}); return; }
    try {
      const d = await A().post("/mind/think", { question: q });
      if (th) th.textContent = d.answer || "—";
      const conf = (d.confidence || 0) * 100, hy = Math.min(100, (d.hypotheses || 0) * 30), gp = Math.min(100, (d.gaps || []).length * 25);
      if (window.AntCognitive) AntCognitive.setActivation({
        planner: 60, researcher: gp || 40, hypothesizer: hy, inference: conf, simulator: 40,
        critic: d.critique_ok ? 70 : 30, verifier: conf, learner: 45, executor: conf,
      });
      if (hyp) hyp.innerHTML = (d.gaps && d.gaps.length)
        ? d.gaps.map((g) => '<div class="card" style="padding:12px;margin-bottom:8px"><div style="font-size:13px">Lacuna a investigar: ' + esc(g) + "</div></div>").join("")
        : '<div class="mono" style="color:var(--dim);font-size:12px">Sem lacunas · confiança ' + (d.confidence ?? "—") + "</div>";
    } catch (e) { if (th) th.textContent = "Colônia adormecida."; }
  }

  async function fillMissions() {
    const box = $("missions-list"); if (!box) return;
    try {
      const d = await A().get("/organism/missions"); const ms = d.missions || [];
      set("nav-mission-count", ms.length || "");
      box.innerHTML = ms.length ? ms.map((m) =>
        '<div class="mission"><div class="mm-h"><h4>' + esc(m.description) + '</h4><span class="mm-state">' +
        (m.runs || 0) + ' execuções</span></div><div class="mono" style="color:var(--dim);font-size:12px;margin-top:6px">frequência: a cada ' +
        (m.frequency || "—") + "h</div></div>").join("")
        : '<div class="mono" style="color:var(--dim);font-size:12px">Nenhuma missão permanente ainda.</div>';
    } catch (e) { box.innerHTML = dorm; }
  }

  const FB = { up: "approve", down: "reject", teach: "teach", pin: "default" };
  function decisionHTML(e) {
    const txt = e.type.replace(/_/g, " ").toLowerCase() + (e.payload && e.payload.goal ? " — " + e.payload.goal : e.payload && e.payload.domain ? " (" + e.payload.domain + ")" : "");
    const time = new Date(e.ts * 1000).toLocaleTimeString().slice(0, 5);
    const b = (fb, ico, t) => '<button data-fb="' + fb + '" title="' + t + '"><svg class="ico sm"><use href="#' + ico + '"/></svg></button>';
    return '<div class="decision"><span class="dt">' + time + '</span><div style="flex:1"><div class="dtxt">' + esc(txt) +
      '</div><div class="dfb">' + b("up", "i-check", "Funcionou") + b("down", "i-x", "Não gostei") +
      b("teach", "i-chat", "Ensinar") + b("pin", "i-target", "Tornar padrão") + "</div></div></div>";
  }

  async function fillQueen() {
    const box = $("queen-decisions");
    try {
      const d = await A().get("/events/history?limit=50");
      const decs = (d.events || []).filter((e) => ["DECISION_TAKEN", "PLAN_CREATED", "TASK_CREATED", "BOT_RECRUITED"].includes(e.type)).slice(-6).reverse();
      if (box) box.innerHTML = decs.length ? decs.map(decisionHTML).join("")
        : '<div class="mono" style="color:var(--dim);font-size:12px">Sem decisões ainda — envie uma tarefa no Chat.</div>';
      wireFeedback();
    } catch (e) { if (box) box.innerHTML = dorm; }
    try { const meta = await A().get("/colony/meta"); set("queen-goals", (meta.observations ?? 0) + " observações"); } catch (e) {}
    try { const dna = await A().get("/organism/dna"); const el = $("queen-dna");
      if (el) el.innerHTML = (dna.traits && dna.traits.length) ? dna.traits.map((t) => '<span class="chip">' + esc(String(t)) + "</span>").join("")
        : '<span class="chip">genoma: ' + (dna.genome_size || 0) + " traços</span>"; } catch (e) {}
  }

  function wireFeedback() {
    document.querySelectorAll(".decision .dfb button[data-fb]").forEach((btn) => {
      if (btn._w) return; btn._w = true;
      btn.addEventListener("click", () => {
        const dec = btn.closest(".decision"); const txt = dec ? (dec.querySelector(".dtxt") || {}).textContent : "";
        btn.parentElement.querySelectorAll("button").forEach((b) => b.classList.remove("chosen"));
        btn.classList.add("chosen");
        A().post("/organism/feedback", { kind: FB[btn.dataset.fb] || "approve", strategy: txt, text: txt }).then((r) => {
          const q = $("queen-learned");
          if (q && r) q.innerHTML = '<div class="chip">"' + esc((r.strategy || txt).slice(0, 36)) + '" · peso ' + (r.weight ?? "ajustado") + (r.blocked ? " · bloqueada" : "") + "</div>" + q.innerHTML;
        }).catch(() => {});
      });
    });
  }

  async function fillTimeline() {
    try {
      const d = await A().get("/events/history?limit=14");
      const IC = { TASK_CREATED: "i-target", BOT_RECRUITED: "i-worker", PLAN_CREATED: "i-crown", RESEARCH_COMPLETED: "i-compass", DECISION_TAKEN: "i-crown", MEMORY_RECALLED: "i-book", ACTION_COMPLETED: "i-check", ACTION_FAILED: "i-x" };
      const CS = { TASK_CREATED: "caste-worker", BOT_RECRUITED: "caste-explorer", PLAN_CREATED: "caste-queen", DECISION_TAKEN: "caste-queen", RESEARCH_COMPLETED: "caste-explorer", MEMORY_RECALLED: "caste-nurse", ACTION_FAILED: "caste-soldier", ACTION_COMPLETED: "caste-worker" };
      const ent = (d.events || []).slice().reverse().filter((e) => IC[e.type]).map((e) => ({
        t: new Date(e.ts * 1000).toLocaleTimeString().slice(0, 5), ico: IC[e.type], caste: CS[e.type] || "caste-worker",
        txt: e.type.replace(/_/g, " ").toLowerCase() + (e.payload && e.payload.goal ? " — " + e.payload.goal : ""),
      }));
      if (window.AntTimeline) AntTimeline.mount("decision-timeline", ent);
    } catch (e) { if (window.AntTimeline) AntTimeline.mount("decision-timeline", null); }
  }

  async function fillConsole() {
    const box = $("console-log"); if (!box) return;
    try {
      const d = await A().get("/events/history?limit=60");
      box.innerHTML = (d.events || []).map((e) => {
        const cls = /FAIL|ERROR/.test(e.type) ? "err" : /COMPLETED/.test(e.type) ? "ok" : /THREAT/.test(e.type) ? "warn" : "info";
        return '<div class="ln ' + cls + '"><span class="lt">' + new Date(e.ts * 1000).toLocaleTimeString() +
          '</span><span class="lc">' + e.type + '</span><span class="lm">' + esc(JSON.stringify(e.payload || {})) + "</span></div>";
      }).join("");
      box.scrollTop = box.scrollHeight;
    } catch (e) { box.innerHTML = '<div class="ln warn"><span class="lc">OFFLINE</span><span class="lm">colônia adormecida</span></div>'; }
  }

  function onTab(name) {
    if (name === "colony" && window.AntDashboard) AntDashboard.mount("org-hierarchy", "colony-network");
    if (name === "cognitive") { if (window.AntCognitive) AntCognitive.mount("cognitive-center"); fillCognition(); }
    if (name === "resources") fillResources();
    if (name === "queen") fillQueen();
    // timeline/console/missions agora são donos do timeline_hub.js (fusão 6.3):
    // seus fills (fillTimeline/fillConsole/fillMissions) seguem definidos aqui
    // como fallback, mas não são mais chamados daqui — evita polling duplicado.
  }

  document.addEventListener("ants:tab", (e) => onTab(e.detail));
  document.addEventListener("ants:task-done", () => { if (document.querySelector('.tab.is-active#tab-cognitive')) fillCognition(); });
  document.addEventListener("ants:online", (e) => { if (e.detail) { fillResources(); } else setDormant(); });

  document.addEventListener("DOMContentLoaded", () => {
    fillResources();
    setInterval(() => {
      const act = document.querySelector(".tab.is-active, .tab.active");
      if (act && act.id === "tab-resources") fillResources();
    }, 5000);
  });
})();
