#!/usr/bin/env bash
# AstroCopilot - inicializador multiplataforma (Mac / Linux / Windows Git Bash)
# Sobe o BACKEND (venv + uvicorn) e o DASHBOARD (npm run dev) juntos.
# Uso:  ./iniciar.sh        (no Windows nativo, use iniciar.bat)
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

# --- aviso se o ffmpeg nao estiver no PATH (necessario p/ voz por arquivo) ---
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[aviso] ffmpeg nao encontrado no PATH."
  echo "        A voz por wake word (navegador) funciona sem ele;"
  echo "        para a voz por arquivo/gravacao instale: macOS 'brew install ffmpeg' | Linux 'sudo apt install ffmpeg'"
fi

echo "==> Subindo backend (http://localhost:8000/docs) ..."
( cd "$ROOT/backend" && . "$ACTIVATE" && exec uvicorn main:app --reload ) &
BACK_PID=$!

echo "==> Subindo dashboard (http://localhost:5173) ..."
( cd "$ROOT/dashboard" && { [ -d node_modules ] || npm install; } && exec npm run dev ) &
DASH_PID=$!

# encerra os dois ao apertar Ctrl+C
cleanup() { echo; echo "Encerrando..."; kill "$BACK_PID" "$DASH_PID" 2>/dev/null; exit 0; }
trap cleanup INT TERM

echo
echo "Pronto! Abra http://localhost:5173 no Chrome ou Edge."
echo "Para parar: Ctrl+C aqui (encerra backend e dashboard)."
wait
