/* Ant's — sse.js (8.0 · D.1): tempo real por Server-Sent Events, aditivo.
 * Expõe AntsSSE.stream(taskId, onData, onEnd): tenta EventSource no endpoint
 * /hive/status/{id}/stream; se o navegador/servidor não suportar, chama
 * onEnd("fallback") e o polling atual (api_bridge) continua valendo. Nunca
 * substitui nem quebra o fluxo existente. Não toca nos 4 JS legados. */
(function () {
  "use strict";
  var AntsSSE = {
    supported: typeof window.EventSource !== "undefined",
    stream: function (taskId, onData, onEnd) {
      if (!this.supported) { if (onEnd) onEnd("fallback"); return null; }
      var url = location.origin + "/hive/status/" + taskId + "/stream";
      var es;
      try { es = new EventSource(url); }
      catch (e) { if (onEnd) onEnd("fallback"); return null; }
      es.onmessage = function (ev) {
        try { if (onData) onData(JSON.parse(ev.data)); } catch (e) {}
      };
      es.addEventListener("end", function () { es.close(); if (onEnd) onEnd("done"); });
      es.addEventListener("error", function () { es.close(); if (onEnd) onEnd("fallback"); });
      return es;
    },
  };
  window.AntsSSE = AntsSSE;
})();
