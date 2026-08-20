/* Ant's — deep_research_ui.js (9.5 · Fase C): botão "Pesquisa profunda".
 * A colônia investiga o tema em várias etapas (sub-perguntas → busca → dedup →
 * verificação → síntese pelo córtex). Sem tocar no chat.js legado: arma a flag
 * window.__antDeep e usa o próprio #chat-send. Também mostra, honestamente, qual
 * córtex está ativo (regras/ollama/api), lido do /health via "ants:health". */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };

  function wire() {
    var btn = $("deep-btn"), input = $("chat-input"), send = $("chat-send");
    if (btn && input && send) {
      btn.addEventListener("click", function () {
        if (!input.value.trim()) { input.focus(); input.placeholder = "Digite um tema para a pesquisa profunda…"; return; }
        window.__antDeep = true;          // api_bridge injeta deep:true
        send.click();
      });
    }
    // Córtex ativo (honesto): atualiza a partir do /health distribuído.
    document.addEventListener("ants:health", function (e) {
      var el = $("deep-cortex"); if (!el) return;
      var r = (e.detail && e.detail.reasoning) || null;
      var map = { rules: "regras", ollama: "Ollama (local)", api: "API" };
      el.textContent = "córtex: " + (r ? (map[r.backend] || r.backend) : "—");
      el.title = r && r.llm ? ("cérebro externo ativo" + (r.model ? " · " + r.model : ""))
        : "raciocínio por regras (offline) — plugue Ollama ou uma chave de API";
    });
  }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", wire);
  else wire();
})();
