/* Ant's — colony_awareness.js (C2 · FASE C): a consciencia da colonia na tela.
 *
 * A FASE A deu a colonia quatro formas de saber sobre si mesma — grafo causal,
 * desempenho proprio, experimentos A/B e calibracao de confianca — e todas
 * viviam SO em endpoints. A autoavaliacao da FASE A registrou isso como divida:
 * "a interface nao mostra nada disso; o dono nao ve a FASE A pela tela".
 *
 * Este painel paga a divida. E, como esses quatro nascem VAZIOS numa instalacao
 * nova, ele e tambem o lugar certo para praticar a regra 6 do protocolo:
 *
 *     painel sem dado nao e preenchido com exemplo; o vazio se EXPLICA.
 *
 * Cada secao vazia diz o que falta acontecer para ela ter conteudo. Nenhuma
 * mostra numero inventado, barra fake ou placeholder decorativo.
 *
 * Aditivo: nao toca nos 4 JS legados nem em ID legado. Sem emoji, sem
 * framework, sem build. Estilo escopado em web/css/colony_awareness.css.
 */
(function () {
  "use strict";

  var KEY = "ants:aware-collapsed";
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  };
  function store(k, v) {
    try {
      if (v === undefined) return localStorage.getItem(k);
      localStorage.setItem(k, v);
    } catch (e) { return null; }
  }

  /* As quatro secoes. `vazio` NAO e texto decorativo: diz o que precisa
   * acontecer para a secao ter conteudo. */
  var SECOES = [
    {
      id: "calibration", url: "/calibration", titulo: "Calibração da confiança",
      vazio: "Nenhuma missão medida ainda. A cada resposta a colônia compara a "
           + "confiança que declarou com o que de fato aconteceu.",
      render: function (d) {
        if (!d || !d.total) return null;
        var linhas = (d.reliability || []).map(function (b) {
          return linha("faixa " + b.bin, "declarou " + pct(b.predicted)
            + " · acertou " + pct(b.observed) + " · " + b.count + " missão(ões)");
        }).join("");
        return linha("missões medidas", String(d.total))
          + linha("desvio (ECE)", String(d.ece)) + linhas;
      }
    },
    {
      id: "self", url: "/self-performance", titulo: "Desempenho próprio",
      vazio: "A colônia ainda não mediu como ela mesma se sai. Depois de "
           + "algumas missões, aparece aqui a taxa por casta e o tempo por rota.",
      render: function (d) {
        if (!d || !d.total) return null;
        var castas = Object.keys(d.formation_hint || {}).map(function (c) {
          return linha(c, pct(d.formation_hint[c]) + " de sucesso");
        }).join("");
        var rotas = (d.routes || []).map(function (r) {
          var t = (d.route_times || {})[r];
          return linha(r, t == null ? "sem tempo medido" : t + "s em média");
        }).join("");
        return linha("missões", String(d.total)) + castas + rotas;
      }
    },
    {
      id: "causal", url: "/causal", titulo: "Grafo causal",
      vazio: "Nenhuma relação causa→efeito observada ainda. O grafo só registra "
           + "o que as missões demonstraram — nunca causalidade suposta.",
      render: function (d) {
        var arestas = (d && d.edges) || [];
        if (!arestas.length) return null;
        return arestas.slice(0, 8).map(function (e) {
          return linha(e.cause + " → " + e.effect,
            (e.observations || e.weight || 0) + " observação(ões)");
        }).join("");
      }
    },
    {
      id: "experiments", url: "/experiments", titulo: "Experimentos A/B",
      vazio: "Nenhum experimento em curso. O dono inicia um comparando duas "
           + "rotas para um tipo de objetivo.",
      render: function (d) {
        var exps = (d && d.experiments) || [];
        if (!exps.length) return null;
        return exps.map(function (x) {
          var v = x.status === "decidido"
            ? "venceu: " + x.winner + " (z=" + x.z + ")"
            : x.status + " — " + x.reason;
          return linha(x.goal_signature || x.id, v);
        }).join("");
      }
    }
  ];

  function pct(v) {
    return (v == null) ? "—" : Math.round(Number(v) * 100) + "%";
  }
  function linha(k, v) {
    return '<div class="ca-row"><span class="ca-k">' + esc(k)
      + '</span><span class="ca-v">' + esc(v) + "</span></div>";
  }

  function shell() {
    var el = document.getElementById("ants-awareness");
    if (el || !document.body) return el;
    el = document.createElement("section");
    el.id = "ants-awareness";
    el.setAttribute("data-collapsed", store(KEY) === "1" ? "1" : "0");
    el.innerHTML =
      '<button class="ca-head" type="button" aria-expanded="'
        + (store(KEY) === "1" ? "false" : "true") + '">'
      + '<span class="ca-title">Consciência da colônia</span>'
      + '<span class="ca-caret" aria-hidden="true"></span></button>'
      + '<div class="ca-body">' + SECOES.map(function (s) {
          return '<div class="ca-sec" data-sec="' + s.id + '">'
            + '<h4 class="ca-sec-t">' + esc(s.titulo) + "</h4>"
            + '<div class="ca-sec-b"><p class="ca-empty">carregando…</p></div>'
            + "</div>";
        }).join("") + "</div>";
    document.body.appendChild(el);
    el.querySelector(".ca-head").addEventListener("click", function () {
      var c = el.getAttribute("data-collapsed") === "1" ? "0" : "1";
      el.setAttribute("data-collapsed", c);
      this.setAttribute("aria-expanded", c === "1" ? "false" : "true");
      store(KEY, c);
    });
    return el;
  }

  function pinta(sec, html, vazio) {
    var alvo = document.querySelector('[data-sec="' + sec + '"] .ca-sec-b');
    if (!alvo) return;
    alvo.innerHTML = html || ('<p class="ca-empty">' + esc(vazio) + "</p>");
  }

  function carrega() {
    if (!shell()) return;
    SECOES.forEach(function (s) {
      fetch(s.url, { headers: { Accept: "application/json" } })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) { pinta(s.id, s.render(d), s.vazio); })
        .catch(function () {
          /* Falha de rede tambem se explica — nao vira secao vazia silenciosa. */
          pinta(s.id, null, "Não consegui falar com o backend agora. "
            + "Esta seção volta assim que a conexão voltar.");
        });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", carrega);
  } else { carrega(); }
  /* Cada missao real muda esses numeros: recarrega depois que ela fecha. */
  document.addEventListener("ants:task-done", function () {
    setTimeout(carrega, 400);
  });
})();
