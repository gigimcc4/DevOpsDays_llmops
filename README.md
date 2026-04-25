# Hands-On LLMOps: Build an Observable AI System in 90 Minutes

A DevOps Days workshop by Dr. Jeanne McClure. / [Ars Innovate Technologies & Consulting](https://arsinnovate.com) & [Data Science and AI Academy, North Carolina State University](https://datascienceacademy.ncsu.edu/)

You ship an LLM feature. It works — mostly. Last week it gave a customer bizarre advice and nobody knows why. The logs show an HTTP 200. Helpful.

LLMs fail differently. There is no stack trace when the model hallucinates. Your APM tools see a successful API call while the output is nonsense. In this workshop you build a full RAG system with production-grade observability from scratch, on your laptop, using only open-source tools with zero API costs.

---

## The stack (all free, all local)

| Tool | Role |
|------|------|
| [Ollama](https://ollama.com) | Runs the LLM and embedding models locally |
| [ChromaDB](https://www.trychroma.com) | In-process vector store |
| [Langfuse](https://langfuse.com) | LLM-native observability (traces, prompts, tokens) |
| [OpenTelemetry](https://opentelemetry.io) | Vendor-neutral distributed tracing |

---

## After the workshop - if you do not have them installed.

**Read and complete [PREWORK.md](./PREWORK.md).** Plan 30–45 minutes. The downloads are the slow part; the setup is about 10 minutes of active work.

When your environment is ready:

```bash
python step0_check/check_env.py
```

Every check should be green.

---

## Workshop layout

Each step lives in its own folder. You can also `git checkout step-N` to jump to the state of the repo at the end of that section.

| Step | Folder | What you add |
|------|--------|--------------|
| 0 | `step0_check/` | Prework verifier (run before workshop) |
| 1 | `step1_rag/` | Minimal RAG pipeline — works, but a black box |
| 2 | `step2_langfuse/` | Langfuse decorators around every stage |
| 3 | `step3_otel/` | OpenTelemetry spans alongside Langfuse |
| 4 | `step4_debug/` | Same code with one planted bug — debug via traces |

Run any step with:

```bash
python stepN_<name>/rag.py
```

---

## After the workshop

Take this home and extend it. The README in each step folder (or the comments at the top of each `rag.py`) tells you what that step adds and why.

Ideas Monday you:
- Swap `ConsoleSpanExporter` for an OTLP exporter to your real APM
- Add an evaluation loop (Langfuse supports LLM-as-judge scoring)
- Replace Ollama with a hosted model — the observability wrapper doesn't change
- Instrument your team's actual RAG service using this pattern

---

## Questions or stuck?

Open an issue on this repo, or find me on [LinkedIn](https://www.linkedin.com/in/drjeannemcclure/) (Dr. Jeanne McClure). I respond.

This material is based in part upon work supported by the National Science Foundation under Grant #DGE-2222148. Any opinions, findings, and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the National Science Foundation.


