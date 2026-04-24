# Prework — Do This Before the Workshop

**Time needed: 30-45 minutes.** Most of that is model downloads; you can walk away while they run.

**Do not skip.** We have 90 minutes together. If you arrive without the stack installed, you will watch instead of build.

---

## What you're installing

| Tool | What it does | Size |
|------|--------------|------|
| Docker Desktop | Runs Langfuse (our observability backend) | ~700 MB |
| Ollama | Runs LLMs locally, no API keys | ~400 MB |
| `llama3.2:1b` | The LLM we'll use in RAG | ~1.3 GB |
| `all-minilm` | The embedding model for vectors | ~46 MB |
| Python 3.10+ | The workshop code is Python | — |
| Python packages | `pip install -r requirements.txt` | ~300 MB |

Total disk: ~3 GB. Total bandwidth: ~3 GB. Do this on your home wifi, not the conference wifi.

---

## Steps

### 1. Clone the repo

```bash
git clone https://github.com/gigimcc4/DevOpsDays_llmops.git
cd DevOpsDays_llmops
```

### 2. Install Docker Desktop

Download from https://www.docker.com/products/docker-desktop and start it. Wait for the whale icon in your menu bar / system tray to stop animating. That means the daemon is running.

Verify:

```bash
docker info
```

No errors, some output about containers — you're good.

### 3. Start Langfuse

From the repo root:

```bash
docker compose up -d
```

First time pulls ~500 MB of images and takes 1-3 minutes. Check it's up:

```bash
curl http://localhost:3000/api/public/health
```

You should see `{"status":"OK"}`. If you don't, wait another minute and try again — Langfuse takes a beat to finish booting.

### 4. Create your Langfuse API key

1. Open http://localhost:3000 in your browser.
2. Log in with: `workshop@local.dev` / `workshop123`
3. Open the **LLMOps Workshop** project (pre-seeded).
4. Go to **Settings → API Keys → Create new API keys**.
5. Copy the Public Key and Secret Key.

Create a `.env` file in the repo root:

```bash
cp .env.example .env
# Then edit .env and paste your keys
```

### 5. Install Ollama

Download from https://ollama.com/download and run the installer. On macOS it adds an `ollama` menu bar icon. On Linux it's a systemd service. Either way, `ollama` is now on your PATH.

### 6. Pull the models

```bash
ollama pull llama3.2:1b
ollama pull all-minilm
```

These run in the background. Do the next step while they download.

### 7. Install Python packages

We recommend a virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate     # macOS/Linux
# .venv\Scripts\activate       # Windows PowerShell
pip install -r requirements.txt
```

### 8. Run the verification script

```bash
python step0_check/check_env.py
```

You want to see **all green checkmarks**. If anything is red, the script tells you the one command to fix it.

---

## If something is broken

Post in the DevOps Days workshop Slack/Discord channel with:
- The OS you're on
- The exact output from `python step0_check/check_env.py`
- What you tried already

Arsinnovate will be watching the channel the day before the workshop.

---

## What we'll actually do in 90 minutes

Once everyone is verified, we move fast:

- **0:00-0:10** — Intro, verify the room is live, explain the arc
- **0:10-0:25** — Step 1: build a minimal RAG pipeline (~80 lines)
- **0:25-0:45** — Step 2: add Langfuse traces, see every prompt/completion
- **0:45-1:05** — Step 3: add OpenTelemetry spans for the cross-service view
- **1:05-1:20** — Step 4: we break the pipeline, you debug it using traces
- **1:20-1:30** — Production patterns, Q&A, where to go next

You will leave with a working repo you can extend at work Monday.
