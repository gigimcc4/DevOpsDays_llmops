# DevOps and LLMOps Glossary

## Observability terms

A trace represents the full journey of a single request through a system. It is composed of one or more spans. In an LLM system, a single user question might produce a trace with spans for: retrieve_context, embed_query, call_llm, format_response.

A span is a named, timed unit of work within a trace. Spans have a start time, an end time, attributes (key-value tags), and events. Parent-child relationships between spans form the trace's shape.

OpenTelemetry (OTel) is the vendor-neutral standard for tracing, metrics, and logs. You instrument your code once using the OTel API, then export to any backend — Jaeger, Tempo, Datadog, Honeycomb — without rewriting instrumentation.

Langfuse is an open-source LLM-specific observability platform. It understands LLM concepts natively: prompts, completions, token counts, model versions, evaluation scores. You can self-host it or use the managed service.

## RAG terms

A vector is a fixed-length array of floating-point numbers that represents the semantic content of text. Similar texts produce vectors that are close together in the embedding space.

ChromaDB is an open-source vector database optimized for embeddings. It runs in-process (like SQLite) or as a server, and supports metadata filtering alongside vector search.

Top-k retrieval returns the k chunks whose embedding vectors are nearest to the query vector. Common values are k=3 to k=10 depending on chunk size and context window budget.

## Ollama

Ollama is a local runtime for open-weight LLMs. You run `ollama pull <model>` to download weights and `ollama run <model>` to chat. It exposes an OpenAI-compatible HTTP API on port 11434, so libraries that expect OpenAI often work unchanged by pointing at http://localhost:11434.

Small models that fit on laptops include llama3.2:1b (1.3GB), phi3:mini (2.3GB), and qwen2.5:0.5b (400MB). Quality scales with size but so do memory and latency.
