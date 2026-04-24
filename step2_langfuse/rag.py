"""
Step 2 — Same RAG, now with Langfuse traces.

What changed from step 1:
  * `from langfuse.decorators import observe, langfuse_context`
  * @observe() on each stage function
  * Inside generate_answer, we attach prompt + completion to the current span
    so Langfuse's LLM UI renders them properly.

Run: python step2_langfuse/rag.py
Then visit http://localhost:3000 and watch the traces light up.

What to notice:
  Every question produces a nested trace:
    ask
    |-- retrieve
    |   `-- embed_text
    `-- generate_answer
  Clicking any span shows inputs, outputs, latency, and (for LLM spans)
  prompt / completion / token usage.
"""
from __future__ import annotations

import os
import pathlib
import sys

import chromadb
import ollama
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.decorators import langfuse_context, observe
from rich.console import Console
from rich.panel import Panel

load_dotenv()
console = Console()

# ---------- Config ----------
LLM_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "all-minilm")
DOCS_DIR = pathlib.Path(__file__).parent.parent / "sample_docs"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 3

# Fail loudly if the API keys aren't set — a silent no-op is the worst
# possible outcome for an observability workshop.
if not os.getenv("LANGFUSE_PUBLIC_KEY") or not os.getenv("LANGFUSE_SECRET_KEY"):
    console.print(
        "[red]Missing LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY. "
        "Copy .env.example to .env and fill in keys from http://localhost:3000[/red]"
    )
    sys.exit(1)

langfuse = Langfuse()  # reads env vars


# ---------- Pipeline stages ----------
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
def embed_text(text: str) -> list[float]:
    r = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    # Tag the span so the Langfuse UI groups embedding calls by model
    langfuse_context.update_current_observation(
        model=EMBED_MODEL,
        metadata={"char_len": len(text)},
    )
    return r["embedding"]


def build_index(chunks: list[dict]) -> chromadb.Collection:
    client = chromadb.EphemeralClient()
    try:
        client.delete_collection("docs")
    except Exception:
        pass
    coll = client.create_collection("docs")

    for i, c in enumerate(chunks):
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
    qvec = embed_text(query)
    res = coll.query(query_embeddings=[qvec], n_results=k)
    hits = [
        {"text": doc, "source": meta["source"], "distance": dist}
        for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]
    # Attach retrieval results so we can inspect them later
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
    r = ollama.generate(model=LLM_MODEL, prompt=prompt)
    response = r["response"].strip()

    # Populate the LLM-specific fields Langfuse understands
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
    console.print(Panel.fit(f"[bold]Q:[/bold] {question}", border_style="cyan"))
    chunks = retrieve(coll, question)
    answer = generate_answer(question, chunks)
    console.print(Panel(answer, title="Answer", border_style="green"))


def main() -> int:
    console.print("[bold]Loading docs...[/bold]")
    docs = load_documents()
    console.print(f"  loaded {len(docs)} documents")

    console.print("[bold]Chunking...[/bold]")
    chunks = chunk_documents(docs)
    console.print(f"  produced {len(chunks)} chunks")

    console.print(f"[bold]Building index...[/bold]")
    coll = build_index(chunks)
    console.print(f"  indexed {coll.count()} chunks\n")

    questions = [
        "What are the three signals unique to LLM systems?",
        "Why is RAG observability not optional?",
        "What does OpenTelemetry give you?",
    ]
    for q in questions:
        ask(coll, q)

    # Flush before exit — otherwise the last traces may not ship
    langfuse.flush()
    console.print("\n[dim]Traces sent. Open http://localhost:3000 to inspect.[/dim]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
