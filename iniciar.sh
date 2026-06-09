#!/usr/bin/env bash
# AstroCopilot - inicializador multiplataforma (Mac / Linux / Windows Git Bash)
# Sobe o BACKEND (em segundo plano, log em arquivo) e o DASHBOARD (primeiro plano).
# Uso:  ./iniciar.sh        (no Windows nativo sem Git Bash, use iniciar.bat)
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$ROOT/backend/backend.log"

# --- localiza o activate do venv (Unix: bin/ ; Windows Git Bash: Scripts/) ---
if [ -f "$ROOT/backend/.venv/bin/activate" ]; then
  ACTIVATE="$ROOT/backend/.venv/bin/activate"
elif [ -f "$ROOT/backend/.venv/Scripts/activate" ]; then
  ACTIVATE="$ROOT/backend/.venv/Scripts/activate"
else
  echo "[erro] venv nao encontrado em backend/.venv"
  echo "Crie com:"
  echo "  cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# --- aviso se o ffmpeg nao estiver no PATH (so a voz por arquivo precisa) ---
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[aviso] ffmpeg ausente: a voz por wake word (navegador) funciona; para voz"
  echo "        por arquivo instale -> macOS: brew install ffmpeg | Linux: sudo apt install ffmpeg"
fi

# --- BACKEND em segundo plano (log em arquivo; sem --reload p/ estabilidade) ---
echo "==> Subindo backend... (log: backend/backend.log)"
( cd "$ROOT/backend" && . "$ACTIVATE" && exec uvicorn main:app --host 127.0.0.1 --port 8000 ) > "$LOG" 2>&1 &
BACK_PID=$!

# encerra o backend ao sair (Ctrl+C ou fim do dashboard)
cleanup() { echo; echo "Encerrando backend..."; kill "$BACK_PID" 2>/dev/null; exit 0; }
trap cleanup INT TERM EXIT

# --- espera o backend ficar de pe (ate ~30s) ---
printf "    aguardando backend"
for i in $(seq 1 30); do
  if curl -s "http://127.0.0.1:8000/" >/dev/null 2>&1; then BACK_OK=1; break; fi
  if ! kill -0 "$BACK_PID" 2>/dev/null; then
    echo; echo "[erro] backend caiu na inicializacao. Ultimas linhas do log:"; tail -15 "$LOG"; exit 1
  fi
  printf "."; sleep 1
done
echo
if [ "${BACK_OK:-0}" = "1" ]; then
  echo "    backend OK -> http://localhost:8000/docs"
else
  echo "[aviso] backend ainda nao respondeu; veja backend/backend.log. Seguindo com o dashboard..."
fi

# --- DASHBOARD em primeiro plano (Vite mostra a URL; Ctrl+C aqui encerra tudo) ---
echo "==> Subindo dashboard -> http://localhost:5173  (abra no Chrome/Edge)"
echo
cd "$ROOT/dashboard"
[ -d node_modules ] || npm install
npm run dev
