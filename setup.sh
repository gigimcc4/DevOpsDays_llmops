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

# Auto-detect any Python 3.10+ on PATH. Macs ship with python3 = 3.9, but
# people often have python3.11 / 3.12 installed via Homebrew or pyenv.
# Pick the first one that's >= 3.10 and use it for the rest of setup.
PYTHON_CMD=""
for py in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$py" >/dev/null 2>&1; then
    if "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
      PYTHON_CMD="$py"
      break
    fi
  fi
done

if [ -z "$PYTHON_CMD" ]; then
  fail "No Python 3.10+ found. Install with one of:
           macOS:  brew install python@3.11
           any:    https://www.python.org/downloads/
         Then re-run ./setup.sh"
fi

if ! command -v docker >/dev/null 2>&1; then
  fail "docker not found. Install Docker Desktop: https://www.docker.com/products/docker-desktop"
fi

PY_VERSION=$("$PYTHON_CMD" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')
ok "Python $PY_VERSION (using $PYTHON_CMD)"

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
if ! "$PYTHON_CMD" -m pip install --upgrade pip >/dev/null 2>&1; then
  warn "pip refused to install (likely externally-managed Homebrew Python) — retrying with --break-system-packages"
  PIP_INSTALL_FLAGS="--break-system-packages"
  "$PYTHON_CMD" -m pip install $PIP_INSTALL_FLAGS --upgrade pip >/dev/null
fi
"$PYTHON_CMD" -m pip install $PIP_INSTALL_FLAGS -r requirements.txt
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
"$PYTHON_CMD" step0_check/check_env.py

echo
echo "${GREEN}${BOLD}Setup complete.${END} You're ready for the workshop."
echo "  Langfuse UI:  http://localhost:3000  (workshop@local.dev / workshop123)"
echo "  Jaeger UI:    http://localhost:16686"
echo "  Run a step:   $PYTHON_CMD step1_rag/rag.py"
echo "  Stop later:   docker compose down"
