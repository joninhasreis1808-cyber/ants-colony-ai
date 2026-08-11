/* Ant's Service Worker — cache offline (PWA). */
const CACHE = "ants-v19";
const ASSETS = [
  "/", "/index.html", "/acesso.html", "/manifest.json",
  "/css/style.css", "/css/design_system.css", "/css/cloud.css",
  "/js/app.js", "/js/scripts.js", "/js/chat.js", "/js/bots.js", "/js/memory.js", "/js/factory.js",
  "/js/notifications.js", "/js/device_permissions.js", "/js/context_engine.js", "/js/live_dashboard.js", "/js/cognitive_center.js", "/js/resource_center.js", "/js/timeline.js",
  "/js/awaken.js", "/js/health_footer.js", "/js/onboarding.js",
  "/js/heatmap.js", "/js/replay.js", "/js/lab_mode.js", "/js/live_panels.js", "/js/api_bridge.js",
  "/js/timeline_hub.js", "/js/live_progress.js", "/js/formations_panel.js", "/js/device_panel.js", "/js/action_ui.js",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  // API: network-first (dados frescos), com fallback ao cache.
  if (["/hive", "/memory", "/factory", "/perceive", "/action", "/bio", "/mind",
       "/colony", "/organism", "/device", "/events", "/health"]
      .some((p) => url.pathname.startsWith(p))) {
    e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
    return;
  }
  // Assets (JS/CSS/HTML): STALE-WHILE-REVALIDATE (9.2) — serve o cache na hora
  // E busca a versão nova em segundo plano, atualizando para o próximo load.
  // Assim um merge NUNCA mais serve código velho (fim da regressão de animação).
  e.respondWith(
    caches.open(CACHE).then((cache) =>
      cache.match(e.request).then((cached) => {
        const fresh = fetch(e.request).then((res) => {
          if (res && res.status === 200 && url.origin === self.location.origin) {
            cache.put(e.request, res.clone());
          }
          return res;
        }).catch(() => cached);
        return cached || fresh;
      })
    )
  );
});
