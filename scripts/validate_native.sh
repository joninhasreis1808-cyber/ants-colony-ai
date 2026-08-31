#!/usr/bin/env bash
# Ant's — kit de validacao do corpo local (etapa 4: validar na maquina).
#
# Com o app (ou o backend) rodando, exercita de ponta a ponta a camada HTTP do
# corpo local: saude, status das capacidades, identidade de dispositivo e emissao
# de grant. Depois imprime o CHECKLIST das acoes FISICAS que so voce confirma no
# app grafico (ler/escrever arquivo, comando, tela, app, entrada).
#
# Uso:  bash scripts/validate_native.sh [http://localhost:PORTA]
# (o app nativo usa porta dinamica; pegue-a nos logs ou passe como argumento)
set -uo pipefail
BASE="${1:-http://localhost:8765}"
ok=0; fail=0
J() { command -v jq >/dev/null 2>&1 && jq -r "$1" 2>/dev/null || cat; }
green() { printf '  \033[32mPASS\033[0m %s\n' "$1"; ok=$((ok+1)); }
red()   { printf '  \033[31mFAIL\033[0m %s\n' "$1"; fail=$((fail+1)); }
get()   { curl -fsS "$BASE$1" 2>/dev/null; }
post()  { curl -fsS -X POST "$BASE$1" -H 'Content-Type: application/json' -d "$2" 2>/dev/null; }

echo "== Ant's · validacao do corpo local =="
echo "alvo: $BASE"
echo

# 1) saude
if get /health | grep -q '"status"'; then green "GET /health"; else red "GET /health (o backend esta rodando?)"; fi

# 2) status das capacidades (espera 6 capacidades nativas)
S="$(get /local-agent/status)"
N="$(echo "$S" | J '.native_capabilities | length')"
if [ "${N:-0}" -ge 6 ]; then green "GET /local-agent/status (6 capacidades)"; else red "status das capacidades ($S)"; fi

# 3) identidade de dispositivo: parear
R="$(post /device-identity/register '{"device_id":"validador","name":"kit"}')"
if echo "$R" | grep -q '"secret"'; then green "POST /device-identity/register (segredo entregue)"; else red "pareamento ($R)"; fi

# 4) grant ligado ao dispositivo
G="$(post /local-agent/grant '{"capability":"CAN_READ_FILES","resource":"/tmp/ants_validador.txt","device_id":"validador"}')"
if echo "$G" | grep -q '"token"'; then green "POST /local-agent/grant (token do dispositivo)"; else red "emissao de grant ($G)"; fi

# 5) calibracao viva exposta
if get /calibration | grep -q '"ece"'; then green "GET /calibration"; else red "GET /calibration"; fi

# limpeza do dispositivo de teste
post /device-identity/revoke '{"device_id":"validador"}' >/dev/null

echo
echo "Camada HTTP: $ok pass, $fail fail."
echo
cat <<'CHECK'
== Checklist das acoes FISICAS (confirme no app grafico) ==
No painel "Corpo Local" (so aparece no app nativo), com escopo/pasta concedidos
e ANTS_ALLOWED_DIRS/ANTS_ALLOWED_APPS/ANTS_INPUT_TOOL definidos:

  [ ] Ler arquivo    -> mostra o conteudo de um arquivo autorizado
  [ ] Escrever       -> sem confirm = previa; com confirm = grava de verdade
  [ ] Rodar comando  -> ex.: "echo oi" retorna stdout
  [ ] Capturar tela  -> gera o .png no destino autorizado
  [ ] Abrir app      -> abre um app da allowlist (ex.: firefox)
  [ ] Controle       -> "move 100 200" / "type oi" / "key ctrl+c" agem no SO

E no painel "Cognicao ao Vivo" (canto): apos uma missao, ver a trilha, o degrau
de fallback, o modo e a barra de calibracao.
CHECK
[ "$fail" -eq 0 ] && exit 0 || exit 1
