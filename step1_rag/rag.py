"""
Step 1 — Minimal RAG pipeline.

Goal: answer questions about our sample_docs/ using:
  * Ollama for LLM + embeddings (all local, free)
  * ChromaDB as the vector store (in-memory)
  * No observability yet — that's step 2 and 3

Run: python step1_rag/rag.py

What to notice:
  The pipeline works. Answers look reasonable.
  But when the model says something weird, you have no way to know:
    - Which chunks were retrieved?
    - How many tokens did it use?
    - How long did each stage take?
    - Did the LLM actually follow our prompt?
  That is what step 2 and step 3 will fix.
"""
from __future__ import annotations

import os
import pathlib
import sys

import chromadb
import ollama
from rich.console import Console
from rich.panel import Panel

console = Console()

# ---------- Config ----------
LLM_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "all-minilm")
DOCS_DIR = pathlib.Path(__file__).parent.parent / "sample_docs"
CHUNK_SIZE = 500  # characters
CHUNK_OVERLAP = 50
TOP_K = 3


# ---------- Pipeline stages ----------
def load_documents() -> list[dict]:
    """Read every .md file in sample_docs/."""
    docs = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        docs.append({"source": path.name, "content": path.read_text()})
    return docs


def chunk_documents(docs: list[dict]) -> list[dict]:
    """Split each doc into overlapping character chunks."""
    chunks = []
    for doc in docs:
        text = doc["content"]
        i = 0
        while i < len(text):
            chunk = text[i : i + CHUNK_SIZE]
            chunks.append({"source": doc["source"], "text": chunk, "offset": i})
            i += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def embed_text(text: str) -> list[float]:
    """Single embedding call to Ollama."""
    r = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return r["embedding"]


def build_index(chunks: list[dict]) -> chromadb.Collection:
    """Embed every chunk and insert into a Chroma collection."""
    client = chromadb.EphemeralClient()
    # Drop and recreate — idempotent across runs
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


def retrieve(coll: chromadb.Collection, query: str, k: int = TOP_K) -> list[dict]:
    """Embed the query, find top-k nearest chunks."""
    qvec = embed_text(query)
    res = coll.query(query_embeddings=[qvec], n_results=k)
    return [
        {"text": doc, "source": meta["source"], "distance": dist}
        for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]


def generate_answer(query: str, context: list[dict]) -> str:
    """Ask the LLM to answer using only the retrieved context."""
    joined = "\n\n".join(
        f"[source: {c['source']}]\n{c['text']}" for c in context
    )
    prompt = (
        "You are a helpful assistant answering questions about LLMOps.\n"
        "Use ONLY the context below. If the context does not answer the question, "
        "say 'I don't have enough information.'\n\n"
        f"Context:\n{joined}\n\n"
        f"Question: {query}\n\nAnswer:"
    )
    r = ollama.generate(model=LLM_MODEL, prompt=prompt)
    return r["response"].strip()


def ask(coll: chromadb.Collection, question: str) -> None:
    """End-to-end query."""
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

    console.print(f"[bold]Building index (embedding each chunk with {EMBED_MODEL})...[/bold]")
    coll = build_index(chunks)
    console.print(f"  indexed {coll.count()} chunks\n")

    # Canonical demo questions
    questions = [
        "What are the three signals unique to LLM systems?",
        "Why is RAG observability not optional?",
        "What does OpenTelemetry give you?",
    ]
    for q in questions:
        ask(coll, q)

    return 0


if __name__ == "__main__":
    sys.exit(main())
