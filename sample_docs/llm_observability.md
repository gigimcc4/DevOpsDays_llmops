# LLM Observability: Why It's Different

Traditional APM tools like Datadog, New Relic, and Dynatrace were built for services where a 200 status code means success. LLM-powered services break this assumption. A model can return a syntactically valid response that is factually wrong, semantically off, or politely refuses a reasonable request. The HTTP layer sees success. The user sees garbage.

## Three signals unique to LLM systems

Token usage per request is the cost signal. Unlike a database query, every LLM call has variable cost depending on prompt length and output length. You need per-request token counts rolled up by endpoint, user cohort, and feature flag to build a cost model that tracks reality.

Prompt and completion content is the quality signal. Without capturing what went in and what came out, you cannot debug why the model answered the way it did. This requires care: completion data often contains PII, so retention policies need thought. Langfuse and similar tools let you mask fields before they persist.

Retrieval context is the grounding signal. For RAG systems, the retrieved chunks are the ground truth the model is supposed to use. If retrieval brought back the wrong documents, the model's "hallucination" is actually obedient behavior on bad inputs. You cannot diagnose this without logging retrieved chunks alongside the final answer.

## When to instrument

Instrument before production. The instinct is to ship first and add observability when something breaks. For LLM systems this is backwards: your first production incident is likely to be a bizarre output with zero context, and you will have no way to reproduce it. Trace from day one.
