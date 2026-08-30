/* Ant's — local_agent_ui.js (9.21 · o ultimo fio): liga a interface ao CORPO.
 * A UI pede um grant assinado ao backend (/local-agent/grant) e o entrega ao
 * corpo nativo via AntNative.execute — que verifica e age sob todas as travas.
 * No modo web (sem corpo), fica dormente e honesto. Aditivo; nao toca no legado.
 *
 * API programatica:  await window.AntLocalAgent.run("CAN_READ_FILES", {resource:"/x"})
 */
(function () {
  "use strict";

  var AntNative = window.AntNative || { available: false, execute: function () {
    return Promise.reject(new Error("ponte nativa ausente")); } };

  function requestGrant(capability, resource, ttlSeconds) {
    return fetch("/local-agent/grant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ capability: capability, resource: resource,
                             ttl_seconds: ttlSeconds || null }),
    }).then(function (res) {
      if (!res.ok) return res.text().then(function (t) {
        throw new Error("grant recusado (" + res.status + "): " + t); });
      return res.json().then(function (j) { return j.token; });
    });
  }

  function run(capability, opts) {
    opts = opts || {};
    var resource = opts.resource || opts.command || "";
    return requestGrant(capability, resource, opts.ttl).then(function (token) {
      var args = {};
      if (opts.content != null) args.content = opts.content;
      if (opts.confirm != null) args.confirm = !!opts.confirm;
      if (opts.command != null) args.command = opts.command;
      return AntNative.execute(token, args);
    });
  }

  window.AntLocalAgent = {
    available: !!AntNative.available,
    requestGrant: requestGrant,
    run: run,
  };

  // --- Painel minimo (so aparece quando o corpo nativo esta presente) -------
  function buildPanel() {
    if (!AntNative.available || !document.body) return;
    var box = document.createElement("div");
    box.id = "local-agent-panel";
    box.style.cssText = "position:fixed;right:14px;bottom:14px;z-index:9999;width:320px;" +
      "background:var(--ant-bg-surface,#1e1810);color:var(--ant-text,#ece3d2);" +
      "border:1px solid var(--border,#3a2f1c);border-radius:10px;padding:12px;" +
      "font:13px system-ui,sans-serif;box-shadow:0 6px 24px rgba(0,0,0,.4)";
    box.innerHTML =
      '<div style="font-weight:600;margin-bottom:8px">Corpo Local — agir no dispositivo</div>' +
      '<select id="la-cap" style="width:100%;margin-bottom:6px">' +
      '  <option value="CAN_READ_FILES">Ler arquivo</option>' +
      '  <option value="CAN_WRITE_FILES">Escrever arquivo</option>' +
      '  <option value="CAN_RUN_COMMAND">Rodar comando</option>' +
      '  <option value="CAN_SCREENSHOT">Capturar tela</option>' +
      '  <option value="CAN_CONTROL_APP">Abrir app</option>' +
      '</select>' +
      '<input id="la-res" placeholder="caminho / comando / app / destino .png" style="width:100%;margin-bottom:6px" />' +
      '<textarea id="la-content" placeholder="conteudo (para escrever)" style="width:100%;height:48px;margin-bottom:6px"></textarea>' +
      '<label style="display:block;margin-bottom:6px"><input type="checkbox" id="la-confirm" /> confirmar (gravar/rodar de verdade)</label>' +
      '<button id="la-run" style="width:100%;padding:6px">Executar</button>' +
      '<pre id="la-out" style="white-space:pre-wrap;max-height:140px;overflow:auto;margin:8px 0 0;font-size:12px"></pre>';
    document.body.appendChild(box);

    var out = box.querySelector("#la-out");
    box.querySelector("#la-run").addEventListener("click", function () {
      var cap = box.querySelector("#la-cap").value;
      var res = box.querySelector("#la-res").value;
      var content = box.querySelector("#la-content").value;
      var confirm = box.querySelector("#la-confirm").checked;
      var opts = { confirm: confirm };
      if (cap === "CAN_RUN_COMMAND") { opts.command = res; }
      else { opts.resource = res; if (cap === "CAN_WRITE_FILES") opts.content = content; }
      out.textContent = "executando...";
      run(cap, opts).then(function (r) {
        out.textContent = JSON.stringify(r, null, 2);
      }).catch(function (e) { out.textContent = "erro: " + e.message; });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", buildPanel);
  } else {
    buildPanel();
  }
})();
