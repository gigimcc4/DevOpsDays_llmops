# RAG Patterns and Failure Modes

Retrieval-Augmented Generation grounds an LLM's answer in documents you control. The promise is reduced hallucination and up-to-date answers without retraining. The reality is that RAG pipelines have more moving parts than they appear to, and each part fails in a distinct way.

## The five stages

Loading reads raw content from source systems — PDFs, Confluence, Notion, a support corpus. The failure mode here is silent truncation: a library reads 200 of 500 pages and returns no error.

Chunking splits documents into retrievable units. Chunks that are too small strip context and force the model to guess. Chunks that are too large waste tokens and bury the relevant passage. Overlap between chunks helps preserve context across boundaries but inflates the index.

Embedding converts each chunk into a vector. The failure mode is model mismatch: if you embed documents with one model and query embeddings with another, retrieval will be nearly random. This fails silently because both embedding calls succeed.

Retrieval finds the top-k chunks nearest to the query vector. Top-k too low misses relevant passages. Top-k too high dilutes the context window with noise. Distance metric matters: cosine similarity and Euclidean distance rank differently, especially for un-normalized embeddings.

Generation synthesizes an answer from retrieved chunks and the original question. The failure mode at this stage is instruction override: the model answers from its training data instead of from the chunks. Prompting discipline — "answer only using the context below, and if the context is insufficient, say so" — is load-bearing.

## Canonical debugging flow

When a RAG answer is wrong, work backwards. First look at the final prompt sent to the model: did retrieval put the right chunks in context? If yes, it is a generation problem — prompt tightening or a stronger model. If no, it is a retrieval problem. Next, look at the retrieved chunks relative to the expected chunks: is the right content in the index at all? If no, it is a loading or chunking problem. If yes but it was not retrieved, it is an embedding or ranking problem.

This flow is impossible without per-stage tracing. This is why observability is not optional for RAG.
