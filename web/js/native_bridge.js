/* Ant's — native_bridge.js (9.18 · FASE 5): a ponte da interface com o CORPO local.
 * No app nativo (Tauri), expõe AntNative para invocar o Local Agent em Rust, que
 * verifica o grant assinado pela Mente Colmeia e age no dispositivo. No modo web
 * (Render), AntNative.available é false — nada é executado no dispositivo (honesto).
 * Aditivo; não toca no chat.js legado. Sem emojis. */
(function () {
  "use strict";
  var hasTauri = typeof window !== "undefined" && !!window.__TAURI__;

  function invoke(cmd, payload) {
    // Tauri v2 expõe o invoke em window.__TAURI__.core.invoke.
    var core = window.__TAURI__ && window.__TAURI__.core;
    if (!core || !core.invoke) return Promise.reject(new Error("Tauri indisponível"));
    return core.invoke(cmd, payload || {});
  }

  window.AntNative = {
    // Este processo é o corpo nativo (pode agir no dispositivo)?
    available: hasTauri,
    runtime: hasTauri ? "native" : "web",

    // Executa uma capacidade pelo Local Agent nativo. O `token` é o grant
    // assinado que o backend (cérebro) emitiu; o Rust valida antes de agir.
    // No modo web, recusa com honestidade — o servidor nunca age no dispositivo.
    execute: function (token, args) {
      if (!hasTauri) {
        return Promise.reject(new Error(
          "modo web: o corpo local (app nativo) não está presente"));
      }
      return invoke("la_execute", { token: token, args: args || null });
    },
  };

  // Sinaliza à interface qual corpo está presente (a UI pode adaptar o rótulo
  // de runtime honestamente: "modo nativo — posso agir" × "modo web — só planejo").
  try {
    document.dispatchEvent(new CustomEvent("ants:runtime",
      { detail: { native: hasTauri } }));
  } catch (e) { /* ambiente sem DOM */ }
})();
