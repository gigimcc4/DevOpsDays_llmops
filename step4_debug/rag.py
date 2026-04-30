"""
Step 4 — Break it and debug it.

This file is IDENTICAL to step3_otel/rag.py except for one planted bug.
Run it, watch the answer to question 2 ("Why is RAG observability not
optional?") come back vague or wrong, and use the traces to figure out why.

Hint: don't read the source first. Read the TRACES first. That is the
whole point of the workshop.

Run: python step4_debug/rag.py
Look for: the retrieve span's output. Something is off about what it
retrieved. Ask yourself: why did it retrieve those chunks for that query?

The answer, and the fix, are in SOLUTION.md (peek only after you've tried).
"""
from __future__ import annotations

import os
import pathlib
import sys
from contextlib import contextmanager

import chromadb
import ollama
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.decorators import langfuse_context, observe
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from rich.console import Console
from rich.panel import Panel

load_dotenv()
console = Console()

LLM_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "all-minilm")
DOCS_DIR = pathlib.Path(__file__).parent.parent / "sample_docs"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 3

OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
resource = Resource.create({"service.name": "llmops-workshop-rag-broken"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True))
)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

if not os.getenv("LANGFUSE_PUBLIC_KEY"):
    console.print("[red]Missing Langfuse keys.[/red]")
    sys.exit(1)
langfuse = Langfuse()


@contextmanager
def otel_span(name: str, **attrs):
    with tracer.start_as_current_span(name) as span:
        for k, v in attrs.items():
            span.set_attribute(k, v)
        yield span


def load_documents() -> list[dict]:
    docs = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        docs.append({"source": path.name, "content": path.read_text()})
    return docs


def chunk_documents(docs: list[dict]) -> list[dict]:
    chunks = []
    for doc in docs:
        text = doc["content"]
        i = 0
        while i < len(text):
            chunk = text[i : i + CHUNK_SIZE]
            chunks.append({"source": doc["source"], "text": chunk, "offset": i})
            i += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


@observe()
def embed_text(text: str, _model_override: str | None = None) -> list[float]:
    model = _model_override or EMBED_MODEL
    with otel_span("embed", model=model, char_len=len(text)):
        r = ollama.embeddings(model=model, prompt=text)
    langfuse_context.update_current_observation(
        model=model, metadata={"char_len": len(text)}
    )
    return r["embedding"]


def build_index(chunks: list[dict]) -> chromadb.Collection:
    with otel_span("build_index", chunk_count=len(chunks)):
        client = chromadb.EphemeralClient()
        try:
            client.delete_collection("docs")
        except Exception:
            pass
        coll = client.create_collection("docs")
        for i, c in enumerate(chunks):
            # Indexed with all-minilm...
            vec = embed_text(c["text"])
            coll.add(
                ids=[f"chunk-{i}"],
                embeddings=[vec],
                documents=[c["text"]],
                metadatas=[{"source": c["source"], "offset": c["offset"]}],
            )
    return coll


@observe()
def retrieve(coll: chromadb.Collection, query: str, k: int = TOP_K) -> list[dict]:
    with otel_span("retrieve", top_k=k, query_len=len(query)) as span:
        # --- THE BUG ---
        # Query embedding uses the LLM model by accident (maybe someone
        # refactored and collapsed the two env vars). Ollama happily returns
        # an embedding from the LLM — same dimensionality, totally different
        # vector space. Retrieval is effectively random.
        qvec = embed_text(query, _model_override=LLM_MODEL)
        # ---------------
        res = coll.query(query_embeddings=[qvec], n_results=k)
        hits = [
            {"text": doc, "source": meta["source"], "distance": dist}
            for doc, meta, dist in zip(
                res["documents"][0], res["metadatas"][0], res["distances"][0]
            )
        ]
        span.set_attribute("hits.sources", ",".join(h["source"] for h in hits))
        span.set_attribute("hits.min_distance", float(min(h["distance"] for h in hits)))
    langfuse_context.update_current_observation(
        output=[{"source": h["source"], "distance": h["distance"]} for h in hits]
    )
    return hits


@observe(as_type="generation")
def generate_answer(query: str, context: list[dict]) -> str:
    joined = "\n\n".join(f"[source: {c['source']}]\n{c['text']}" for c in context)
    prompt = (
        "You are a helpful assistant answering questions about LLMOps.\n"
        "Use ONLY the context below. If the context does not answer the question, "
        "say 'I don't have enough information.'\n\n"
        f"Context:\n{joined}\n\n"
        f"Question: {query}\n\nAnswer:"
    )
    with otel_span("llm.generate", model=LLM_MODEL, prompt_chars=len(prompt)) as span:
        r = ollama.generate(model=LLM_MODEL, prompt=prompt)
        response = r["response"].strip()
        span.set_attribute("tokens.input", r.get("prompt_eval_count", 0))
        span.set_attribute("tokens.output", r.get("eval_count", 0))

    langfuse_context.update_current_observation(
        model=LLM_MODEL,
        input=prompt,
        output=response,
        usage={
            "input": r.get("prompt_eval_count", 0),
            "output": r.get("eval_count", 0),
            "unit": "TOKENS",
        },
    )
    return response


@observe()
def ask(coll: chromadb.Collection, question: str) -> None:
    with otel_span("ask", question=question[:120]):
        console.print(Panel.fit(f"[bold]Q:[/bold] {question}", border_style="cyan"))
        chunks = retrieve(coll, question)
        answer = generate_answer(question, chunks)
        console.print(Panel(answer, title="Answer", border_style="green"))


def main() -> int:
    console.print("[bold]Loading docs...[/bold]")
    docs = load_documents()
    console.print("[bold]Chunking...[/bold]")
    chunks = chunk_documents(docs)
    console.print("[bold]Building index...[/bold]")
    coll = build_index(chunks)
    console.print(f"  indexed {coll.count()} chunks\n")

    for q in [
        "What are the three signals unique to LLM systems?",
        "Why is RAG observability not optional?",
        "What does OpenTelemetry give you?",
    ]:
        ask(coll, q)

    langfuse.flush()
    provider.force_flush()
    console.print(
        "\n[dim]Jaeger UI:    http://localhost:16686  (service = llmops-workshop-rag-broken)[/dim]"
    )
    console.print(
        "[dim]Langfuse UI:  http://localhost:3000[/dim]"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
