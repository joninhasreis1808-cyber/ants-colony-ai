/* Ant's Service Worker — cache offline (PWA). */
const CACHE = "ants-v8";
const ASSETS = [
  "/", "/index.html", "/acesso.html", "/manifest.json",
  "/css/style.css", "/css/design_system.css", "/css/cloud.css",
  "/js/app.js", "/js/scripts.js", "/js/chat.js", "/js/bots.js", "/js/memory.js", "/js/factory.js",
  "/js/notifications.js", "/js/device_permissions.js", "/js/context_engine.js", "/js/live_dashboard.js", "/js/cognitive_center.js", "/js/resource_center.js", "/js/timeline.js",
  "/js/awaken.js", "/js/health_footer.js", "/js/onboarding.js",
  "/js/heatmap.js", "/js/replay.js", "/js/lab_mode.js", "/js/live_panels.js",
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
  const url = new URL(e.request.url);
  // API: network-first (dados frescos), com fallback ao cache.
  if (["/hive", "/memory", "/factory", "/perceive", "/action", "/bio", "/mind", "/colony", "/health"]
      .some((p) => url.pathname.startsWith(p))) {
    e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
    return;
  }
  // Assets: cache-first.
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
