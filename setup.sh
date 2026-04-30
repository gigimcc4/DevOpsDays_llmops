#!/usr/bin/env bash
# LLMOps Workshop — One-shot setup (Mac / Linux / WSL)
#
# Installs everything that can be scripted:
#   * Ollama (if missing)
#   * llama3.2:1b + all-minilm models
#   * Python packages from requirements.txt
#   * Langfuse via docker compose
#
# ASSUMES you've already installed:
#   * Python 3.10+   (https://www.python.org/downloads/)
#   * Docker Desktop (https://www.docker.com/products/docker-desktop)
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
#
# Re-running is safe — every step is idempotent.

set -e

GREEN=$'\033[92m'
RED=$'\033[91m'
YELLOW=$'\033[93m'
BOLD=$'\033[1m'
END=$'\033[0m'

step() { echo; echo "${BOLD}==> $1${END}"; }
ok()   { echo "  ${GREEN}[OK]${END}   $1"; }
warn() { echo "  ${YELLOW}[WARN]${END} $1"; }
fail() { echo "  ${RED}[FAIL]${END} $1"; exit 1; }

# ---------------------------------------------------------------------------
# 1. Verify prereqs that we will NOT auto-install
# ---------------------------------------------------------------------------
step "Checking prerequisites (Python + Docker)"

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 not found. Install Python 3.10+ first: https://www.python.org/downloads/"
fi
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
PY_MICRO=$(python3 -c 'import sys; print(sys.version_info.micro)')
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
  fail "Python ${PY_MAJOR}.${PY_MINOR} is too old (need 3.10+)"
fi
ok "Python ${PY_MAJOR}.${PY_MINOR}.${PY_MICRO}"

if ! command -v docker >/dev/null 2>&1; then
  fail "docker not found. Install Docker Desktop: https://www.docker.com/products/docker-desktop"
fi
if ! docker info >/dev/null 2>&1; then
  fail "Docker daemon not running. Start Docker Desktop, then re-run ./setup.sh"
fi
ok "Docker daemon is running"

# ---------------------------------------------------------------------------
# 2. Ollama
# ---------------------------------------------------------------------------
step "Ollama"

if ! command -v ollama >/dev/null 2>&1; then
  warn "Ollama not found — installing"
  case "$OSTYPE" in
    darwin*|linux-gnu*)
      curl -fsSL https://ollama.com/install.sh | sh
      ok "Ollama installed"
      ;;
    *)
      fail "Auto-install only supported on Mac/Linux. Download manually: https://ollama.com/download"
      ;;
  esac
else
  ok "Ollama already installed"
fi

# Make sure the Ollama service is reachable (Mac launches it on install,
# Linux sometimes needs a manual nudge).
if ! curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
  warn "Ollama service not responding — starting it in the background"
  nohup ollama serve >/dev/null 2>&1 &
  for i in 1 2 3 4 5 6 7 8 9 10; do
    sleep 1
    if curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
      ok "Ollama service is up"
      break
    fi
    if [ "$i" -eq 10 ]; then
      fail "Ollama did not start. Try: ollama serve (in a separate terminal)"
    fi
  done
else
  ok "Ollama service is up"
fi

# ---------------------------------------------------------------------------
# 3. Pull models (idempotent — Ollama skips if already cached)
# ---------------------------------------------------------------------------
step "Pulling models (~1.5 GB total, first run only)"
ollama pull llama3.2:1b
ok "llama3.2:1b ready"
ollama pull all-minilm
ok "all-minilm ready"

# ---------------------------------------------------------------------------
# 4. Python packages
# ---------------------------------------------------------------------------
# Modern Homebrew Python (PEP 668) refuses pip-install without permission.
# Try a normal install first; if it fails with "externally-managed-environment",
# retry with --break-system-packages. The flag is harmless on regular Python.
step "Installing Python packages"
PIP_INSTALL_FLAGS=""
if ! python3 -m pip install --upgrade pip >/dev/null 2>&1; then
  warn "pip refused to install (likely externally-managed Homebrew Python) — retrying with --break-system-packages"
  PIP_INSTALL_FLAGS="--break-system-packages"
  python3 -m pip install $PIP_INSTALL_FLAGS --upgrade pip >/dev/null
fi
python3 -m pip install $PIP_INSTALL_FLAGS -r requirements.txt
ok "Python packages installed"

# ---------------------------------------------------------------------------
# 5. Langfuse (docker compose)
# ---------------------------------------------------------------------------
step "Starting Langfuse via docker compose"
docker compose up -d

echo "  Waiting for Langfuse to be reachable on http://localhost:3000 ..."
for i in $(seq 1 30); do
  if curl -fsS http://localhost:3000/api/public/health >/dev/null 2>&1; then
    ok "Langfuse is up at http://localhost:3000"
    break
  fi
  sleep 2
  if [ "$i" -eq 30 ]; then
    fail "Langfuse didn't come up after 60s. Inspect with: docker compose logs langfuse"
  fi
done

# ---------------------------------------------------------------------------
# 6. Final verification
# ---------------------------------------------------------------------------
step "Running env check"
python3 step0_check/check_env.py

echo
echo "${GREEN}${BOLD}Setup complete.${END} You're ready for the workshop."
echo "  Langfuse UI:  http://localhost:3000  (workshop@local.dev / workshop123)"
echo "  Stop Langfuse later with: docker compose down"
