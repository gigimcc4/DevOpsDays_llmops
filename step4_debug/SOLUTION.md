# Step 4 Solution — Instructor Notes

## The bug

In `retrieve()`, the query is embedded with `LLM_MODEL` (an LLM model) instead of `EMBED_MODEL` (a dedicated embeddings model). Documents were embedded with `all-minilm`, queries with `llama3.2:1b`. Ollama happily returns an embedding from a chat model, but the vector spaces do not match, so nearest-neighbor search is essentially random.

```python
# Broken
qvec = embed_text(query, _model_override=LLM_MODEL)

# Fixed
qvec = embed_text(query)  # uses EMBED_MODEL via default
```

## Why it's the right workshop bug

It is silent — no exception, HTTP 200 everywhere, Ollama returns valid-looking floats. It is plausible — a junior engineer collapsing two environment variables into one is exactly how this happens in the wild. The fix is one line. The diagnosis is impossible without the right signal.

## How the traces reveal it

**In Langfuse** (http://localhost:3000):
1. Open any trace.
2. Expand `retrieve -> embed`. Look at the `model` attribute — it says `llama3.2:1b` instead of `all-minilm`.
3. Expand the sibling `embed` spans from indexing (look at the `build_index` trace) — those say `all-minilm`.
4. Mismatch identified in ~30 seconds.

**In OTel console spans**: Same signal — the `embed` span's `model` attribute differs between indexing and querying. `grep model= <console output>` makes it obvious.

**Secondary signals** (useful teaching moments):
- `hits.min_distance` in the retrieve span will be wildly higher than in step 3. Distances near 1.0+ when they used to be 0.3–0.6 is a smell.
- In Langfuse, the retrieved sources list won't correlate with the question — e.g. asking about observability returns chunks from the glossary's Ollama section.

## How to drive the debug flow live

1. Run `python step4_debug/rag.py`. Let everyone see a wrong/vague answer.
2. Ask the room: "What's different? The code looks fine. Did the model get dumber?"
3. Open Langfuse together. Click the bad trace. Narrate: "answer says X, context says… huh, the context is about Y. Where did Y come from?"
4. Walk into the retrieve span. Show the model attribute. Let someone in the room say "that's an LLM, not an embedder" — that's the moment.
5. Fix the line, rerun, show green traces. Victory lap.

## If the traces don't show the bug clearly

Some small embedding models are robust enough that mismatched retrieval still returns the right chunks by luck. If the demo looks too correct, you can make it worse by either:
- Using `qwen2.5:0.5b` as the `_model_override` (even more dimensional mismatch), or
- Changing `TOP_K=3` to `TOP_K=1` (no safety margin from overlap).

## Rollback for participants

If a participant wants a clean, correct pipeline to keep working from, they can:
```bash
git checkout step-3        # fully instrumented, no bug
# or
cp step3_otel/rag.py step4_debug/rag.py
```
