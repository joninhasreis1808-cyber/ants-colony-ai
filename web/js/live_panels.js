/* Ant's — live_panels.js: liga os painéis do design aos endpoints reais.
   Aditivo, só UI. Monta os módulos vivos por aba e injeta dados do backend
   (recursos, console, linha do tempo, feedback da Rainha). Sem emojis. */
(function () {
  "use strict";
  const api = location.origin;
  const $ = (id) => document.getElementById(id);
  const j = (p, o) => fetch(api + p, o || { cache: "no-store" })
    .then((r) => (r.ok ? r.json() : null)).catch(() => null);

  const EV_ICON = {
    TASK_CREATED: "i-target", BOT_RECRUITED: "i-worker", PLAN_CREATED: "i-crown",
    RESEARCH_COMPLETED: "i-compass", DECISION_TAKEN: "i-crown",
    MEMORY_RECALLED: "i-book", ACTION_COMPLETED: "i-check", ACTION_FAILED: "i-x",
  };
  const EV_CASTE = {
    TASK_CREATED: "caste-worker", BOT_RECRUITED: "caste-explorer",
    PLAN_CREATED: "caste-queen", DECISION_TAKEN: "caste-queen",
    RESEARCH_COMPLETED: "caste-explorer", MEMORY_RECALLED: "caste-nurse",
    ACTION_FAILED: "caste-soldier", ACTION_COMPLETED: "caste-worker",
  };

  function fillResources() {
    j("/health").then((h) => {
      if (!h) return;
      if ($("stat-bots")) $("stat-bots").textContent = h.bots_active ?? "—";
      if ($("stat-tasks")) $("stat-tasks").textContent = h.tasks_submitted ?? 0;
      if ($("stat-uptime")) {
        const s = Math.floor(h.uptime_seconds || 0);
        $("stat-uptime").textContent =
          String((s / 60) | 0).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0");
      }
      if ($("nav-bot-count")) $("nav-bot-count").textContent = h.bots_active ?? "";
    });
    j("/organism/vitals").then((v) => {
      const src = (v && (v.vitals || v)) || {};
      const vals = {
        cpu: src.cpu ?? src.cpu_percent, ram: src.ram ?? src.memory ?? src.ram_percent,
        disk: src.disk ?? src.disk_percent, net: src.net ?? src.network,
        battery: src.battery ?? src.energy,
      };
      if (window.AntResources) AntResources.mount("resource-center", vals);
      if (window.AntResources) AntResources.mount("network-center", { net: vals.net });
    });
  }

  function fillTimeline() {
    j("/events/history?limit=14").then((d) => {
      const evs = (d && d.events || []).slice().reverse()
        .filter((e) => EV_ICON[e.type]);
      const entries = evs.map((e) => ({
        t: new Date(e.ts * 1000).toLocaleTimeString().slice(0, 5),
        ico: EV_ICON[e.type], caste: EV_CASTE[e.type] || "caste-worker",
        txt: (e.type.replace(/_/g, " ").toLowerCase()) +
          (e.payload && e.payload.goal ? " — " + e.payload.goal : ""),
      }));
      if (window.AntTimeline && entries.length) AntTimeline.mount("decision-timeline", entries);
    });
  }

  function fillConsole() {
    const box = $("console-log");
    if (!box) return;
    j("/events/history?limit=60").then((d) => {
      const evs = (d && d.events || []);
      box.innerHTML = evs.map((e) => {
        const cls = e.type.includes("FAIL") || e.type.includes("ERROR") ? "err"
          : e.type.includes("COMPLETED") ? "ok"
          : e.type.includes("THREAT") ? "warn" : "info";
        const t = new Date(e.ts * 1000).toLocaleTimeString();
        return '<div class="ln ' + cls + '"><span class="lt">' + t +
          '</span><span class="lc">' + e.type + '</span><span class="lm">' +
          JSON.stringify(e.payload || {}) + "</span></div>";
      }).join("");
      box.scrollTop = box.scrollHeight;
    });
  }

  const FB = { up: "approve", down: "reject", teach: "teach", pin: "default" };
  function wireFeedback() {
    document.querySelectorAll(".decision .dfb button[data-fb]").forEach((btn) => {
      if (btn._wired) return; btn._wired = true;
      btn.addEventListener("click", () => {
        const dec = btn.closest(".decision");
        const txt = dec ? (dec.querySelector(".dtxt") || {}).textContent : "";
        btn.parentElement.querySelectorAll("button").forEach((b) => b.classList.remove("chosen"));
        btn.classList.add("chosen");
        j("/organism/feedback", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ kind: FB[btn.dataset.fb] || "approve", strategy: txt, detail: txt }),
        }).then((r) => {
          const box = $("queen-learned");
          if (box && r) box.innerHTML = '<div class="chip">estratégia "' +
            (r.strategy || txt).slice(0, 40) + '" · peso ' + (r.weight ?? "ajustado") +
            (r.blocked ? " · bloqueada" : "") + "</div>" + box.innerHTML;
        });
      });
    });
  }

  function onTab(name) {
    if (name === "colony" && window.AntDashboard) AntDashboard.mount("org-hierarchy", "colony-network");
    if (name === "cognitive" && window.AntCognitive) AntCognitive.mount("cognitive-center");
    if (name === "resources") fillResources();
    if (name === "timeline") fillTimeline();
    if (name === "console") fillConsole();
    if (name === "queen") wireFeedback();
  }

  document.addEventListener("ants:tab", (e) => onTab(e.detail));
  document.addEventListener("DOMContentLoaded", () => {
    fillResources();
    wireFeedback();
    const clr = $("console-clear");
    if (clr) clr.addEventListener("click", () => { if ($("console-log")) $("console-log").innerHTML = ""; });
    setInterval(() => {
      const act = document.querySelector(".tab.is-active, .tab.active");
      if (act && act.id === "tab-console") fillConsole();
      if (act && act.id === "tab-resources") fillResources();
    }, 5000);
  });
})();
