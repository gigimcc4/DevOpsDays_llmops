# Hands-On(ish) LLMOps: Maybe Build · Maybe Demo of an Observable AI System in 90 Minutes

A DevOpsDays workshop by Dr. Jeanne McClure / [Ars Innovate Technologies & Consulting](https://arsinnovate.com) & [Data Science and AI Academy, North Carolina State University](https://datascienceacademy.ncsu.edu/)

You ship an LLM feature. It works — mostly. Last week it gave a customer bizarre advice and nobody knows why. The logs show an HTTP 200. Helpful.

LLMs fail differently. There is no stack trace when the model hallucinates. Your APM tools see a successful API call while the output is nonsense. In this workshop you build a full RAG system with production-grade observability from scratch, on your laptop, using only open-source tools with zero API costs.

The **(ish)** is on purpose: most participants are seeing this for the first time when they walk in. If your laptop catches up, you build along live. If it doesn't, you become a demo-watcher today and run the workshop tonight at home — your packet keeps you in the game either way.

---

## 📄 Participant packet

Print-ready guide with prerequisites, step-by-step setup, fillable worksheets per step, and a golden-answer key at the back:

**[📄 Get your own copy of the workshop packet (Google Doc)](https://docs.google.com/document/d/1raYxBV0UJqx8_lrNEesVgQl8GgNYo2QZctaV1rQeWHM/copy)** — clicking the link makes a personal editable copy in your Drive, ready to fill in during the workshop

Or grab the file directly: [`workshop_packet/Hands-On-ish_LLMOps_Packet.pdf`](workshop_packet/Hands-On-ish_LLMOps_Packet.pdf)

---

## The stack (all free, all local)

| Tool | Role |
|------|------|
| [Ollama](https://ollama.com) | Runs the LLM and embedding models locally |
| [ChromaDB](https://www.trychroma.com) | In-process vector store |
| [Langfuse](https://langfuse.com) | LLM-native observability — prompts, completions, tokens, costs |
| [OpenTelemetry](https://opentelemetry.io) | Vendor-neutral distributed tracing |
| [Jaeger](https://www.jaegertracing.io) | Clickable OTel trace UI for cross-service debugging |

---

## Quick start

**Prerequisites you need to have installed yourself:**
- Python 3.10 or newer (`brew install python@3.11` on macOS, or [python.org](https://www.python.org/downloads/))
- Docker Desktop ([download here](https://www.docker.com/products/docker-desktop))

`setup.sh` handles everything else — Ollama, models, Python packages, Langfuse, and Jaeger.

**Clone and run:**

```bash
git clone https://github.com/gigimcc4/DevOpsDays_llmops.git
cd DevOpsDays_llmops
chmod +x setup.sh
./setup.sh
```

**When setup completes you'll have:**

- Langfuse UI at <http://localhost:3000> (login: `workshop@local.dev` / `workshop123`)
- Jaeger UI at <http://localhost:16686>
- Ollama serving `llama3.2:1b` and `all-minilm` on port 11434

**Get your Langfuse API keys before Step 2:**

1. Open <http://localhost:3000> and log in
2. Settings (gear icon) → API Keys → Create new API key
3. Rename `.env.example` to `.env` and paste your `pk-lf-...` and `sk-lf-...` keys

---

## Workshop layout

Each step builds on the last. You can also `git checkout step-N` to jump to the state of the repo at the end of that section.

| Step | Folder | What you add |
|------|--------|--------------|
| 0 | `step0_check/` | Prework verifier (run after `setup.sh`) |
| 1 | `step1_rag/` | Minimal RAG pipeline — works, but a black box |
| 2 | `step2_langfuse/` | Langfuse decorators around every stage — full LLM-native traces |
| 3 | `step3_otel/` | OpenTelemetry spans + Jaeger UI — vendor-neutral cross-service view |
| 4 | `step4_debug/` | Same code with one planted bug — debug via traces |

Run any step with:

```bash
python3 stepN_<name>/rag.py
```

(Use `python3.11` or `python3.12` explicitly if your system `python3` is older than 3.10.)

---

## After the workshop — Monday checklist

Take this home and extend it. The README in each step folder (or comments at the top of each `rag.py`) tells you what that step adds and why.

Pick **one** for next week:

- Wrap one LLM call in your codebase with `@observe()` and point Langfuse at it
- Swap the OTLP exporter from local Jaeger to your existing APM (Datadog, Honeycomb, Tempo, New Relic — same env var)
- Write down your three target signals (cost, quality, grounding) in your team's runbook
- Add a Langfuse evaluation loop with LLM-as-judge scoring
- Replace Ollama with a hosted model — the observability wrappers don't change
- Mask PII in prompts/completions before persisting (Langfuse `mask` hook)

---

## Want to go further?

I help engineering teams ship observable AI without learning every lesson the hard way. Three flavors:

- **Stand up your AI stack — observable from day one.** Best fit for engineering managers and tech leads who got the "add AI" task and need to ship without re-living everyone else's first-incident pain.
- **AI orchestration audits + roadmap reviews.** Best fit for architects, SREs, and platform teams who have inherited or are scaling AI workloads.
- **Subcontract / partner.** Best fit for consulting firms and boutique agencies expanding their AI services without hiring full-time.

📧 [jmcclure@arsinnovate.com](mailto:jmcclure@arsinnovate.com) · 💼 [LinkedIn](https://www.linkedin.com/in/jeannemcclure/) · 🌐 [arsinnovate.com](https://arsinnovate.com)

---

## How to cite

If you use these materials in a paper, talk, blog post, internal training, or course, please cite:

> McClure, J. (2026). *Hands-On(ish) LLMOps: Maybe Build · Maybe Demo of an Observable AI System in 90 Minutes.* DevOpsDays Raleigh workshop. Ars Innovate Technologies & Consulting. https://github.com/gigimcc4/DevOpsDays_llmops

BibTeX:

```bibtex
@misc{mcclure2026llmops,
  author       = {McClure, Jeanne},
  title        = {Hands-On(ish) LLMOps: Maybe Build $\cdot$ Maybe Demo of an Observable AI System in 90 Minutes},
  year         = {2026},
  publisher    = {Ars Innovate Technologies \& Consulting},
  howpublished = {DevOpsDays Raleigh workshop},
  url          = {https://github.com/gigimcc4/DevOpsDays_llmops}
}
```

---

## License

**Code** (everything in `step*/`, `setup.sh`, `docker-compose.yml`, `requirements.txt`, env-check scripts) — released under the **MIT License** (see [LICENSE](./LICENSE)). Use, modify, embed in your own projects freely.

**Workshop materials** (slide deck, participant packet, instructor materials, and any derivative training content) — © 2026 Jeanne McClure / Ars Innovate Technologies & Consulting. Released for **non-commercial educational use with attribution**.

You **may**:
- Use the deck, packet, and curriculum to learn at your own pace
- Run this workshop **internally for your own team** (free, with attribution to Jeanne McClure / Ars Innovate)
- Adapt or excerpt for academic teaching, with attribution

You **may not** (without a separate license):
- Charge attendees for a workshop based on this material
- Repackage as a paid course, book, video series, or commercial training
- Use as part of a paid consulting engagement to deliver training to a third party
- Remove attribution

### Commercial / paid use — contact me first

If you want to use these materials for any of the following, please reach out so we can scope a license:
- Paid training / paid workshops / corporate training contracts
- Inclusion in a paid course, certification program, or curriculum
- Integration into a commercial product or service offering
- Derivative works sold for profit

📧 [jmcclure@arsinnovate.com](mailto:jmcclure@arsinnovate.com) · 💼 [LinkedIn](https://www.linkedin.com/in/jeannemcclure/)

I'm friendly. Most reasonable requests get a quick yes with simple terms.

---

## Questions or stuck?

Open an issue on this repo, or find me on [LinkedIn](https://www.linkedin.com/in/jeannemcclure/) (Dr. Jeanne McClure). I respond.

This material is based in part upon work supported by the National Science Foundation under Grant #DGE-2222148. Any opinions, findings, and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the National Science Foundation.
