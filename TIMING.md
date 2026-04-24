# Timing — What we measured, what we budgeted

## Measured (sandbox, Python-only, mocked Ollama)

These numbers isolate Python + ChromaDB + Langfuse + OTel overhead. They do NOT include LLM/embedding inference time.

| Step | Overhead per full run (3 questions) |
|------|-------------------------------------|
| step1_rag | 0.35 s |
| step2_langfuse | 0.29 s |
| step3_otel | 0.13 s |
| step4_debug | 0.12 s |

Implication: the Langfuse/OTel instrumentation adds effectively zero latency on top of the existing pipeline. The budget is all inference.

## Estimated (real workshop laptop, llama3.2:1b + all-minilm)

Per full run (3 questions, 20 index chunks):

| Call | Count | ~Latency each | Subtotal |
|------|-------|---------------|----------|
| all-minilm embed (index) | ~20 | 20-40 ms | ~0.5 s |
| all-minilm embed (query) | 3 | 20-40 ms | ~0.1 s |
| llama3.2:1b generate | 3 | 2-4 s (150 tok @ 50 tok/s) | 6-12 s |
| **Per run total** | | | **7-13 s** |

Expect ~10 s per run on a mid-range laptop. Double that on Intel machines without a discrete GPU. Half that on Apple Silicon.

## 90-minute workshop budget

| Time | Section | Why this length |
|------|---------|-----------------|
| 0:00-0:08 | Intro + verify room is live (`check_env.py`) | Short. Most people did prework. Fix the stragglers fast or pair them with neighbors. |
| 0:08-0:23 | **Step 1 — minimal RAG** (15 min) | Explain (5), code together (6), run (2), discuss answers (2). |
| 0:23-0:43 | **Step 2 — Langfuse** (20 min) | This is the wow moment. Code (5), run (2), tour the Langfuse UI together (10), discuss (3). |
| 0:43-0:58 | **Step 3 — OpenTelemetry** (15 min) | Faster pace — it's the same pattern in a second backend. Code (5), run (2), read spans (5), discuss (3). |
| 0:58-1:18 | **Step 4 — break and debug** (20 min) | Run the broken version (2), let them stare at wrong answers (2), open traces together (5), Socratic debug (8), fix + rerun (3). |
| 1:18-1:30 | Production patterns + Q&A (12 min) | Where to go next, OTLP exporter swap, evaluation loops, linking to their own APM. |
| **Total** | **90 min** | |

## Slack management

Built-in slack: 2-3 minutes across transitions. If you're running hot by step 3:
- Shorten step 3 explanation — participants have the code, they can read later
- Skip the "tour the OTel console output line by line" bit
- Compress Q&A to 5 min, push remaining questions to Slack channel / the repo's issue tracker

If you're running cold (ahead of schedule):
- Deep-dive on a specific trace in Langfuse
- Discuss cost models: given these token counts, what would this look like on GPT-4o?
- Walk through `SOLUTION.md` and talk about other bugs you'd plant

## Red flags to watch for

**Docker not running on someone's laptop:** 10+ min to fix. Pair them with a neighbor, don't burn room time. Give them a fallback — `docker compose up langfuse-db langfuse` as separate containers if full compose fails.

**Ollama model not pulled:** 2-5 min download on conference wifi if lucky, hopeless if not. If more than one person is in this state, have them share a laptop or read along.

**Langfuse keys not set:** 30-second fix. Walk the room through `cp .env.example .env` and "go to localhost:3000, settings, API keys."

**Answers look too good:** if the bug in step 4 produces apparently-correct answers anyway (small model got lucky), swap `_model_override=LLM_MODEL` for `_model_override="qwen2.5:0.5b"` or drop `TOP_K` to 1.
