*This project has been created as part of the 42 curriculum by fcaval.*

# 🤖 RAG against the machine

> *"Will you answer my questions?"*

## 📖 Description

This project implements a **Retrieval-Augmented Generation (RAG) system** that answers questions about the [vLLM](https://github.com/vllm-project/vllm) codebase.

Instead of retraining a language model on new data, the system gives the model access to an external knowledge source — here, the vLLM repository (~3000 files, code + documentation). For each question, the system retrieves the most relevant passages, injects them into the model's context, and generates an answer grounded in those passages rather than the model's internal (and often outdated) knowledge.

**The pipeline does four things:**
1. 📥 **Ingest** the vLLM repository and build a searchable knowledge base
2. 🔍 **Search** that knowledge base to find relevant code/doc snippets for a given question
3. 💬 **Answer** questions using an LLM (`Qwen/Qwen3-0.6B`) grounded in the retrieved context
4. 📊 **Evaluate** retrieval quality using recall@k metrics against a ground-truth dataset

## ⚙️ Instructions

### Prerequisites
- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) installed

### Installation
```bash
git clone <your-repo>
cd <your-repo>
make
```

### Data setup 📦
Place `vllm-0.10.1.zip` in `data/raw/`:
```
data/raw/vllm-0.10.1.zip
```
The zip is extracted automatically on first indexing.

### Usage 🚀

**1. Index the repository** 📥
```bash
uv run python -m student index
```

**2. Answer a single question** 💬
```bash
uv run python -m student answer "How to configure OpenAI server?" --k 10
```

**3. Search without generating an answer** 🔍
```bash
uv run python -m student search "What is PagedAttention?" --k 5
```

**4. Process a full dataset** 📂
```bash
make search_dataset
```

**5. Generate answers from search results** ✨
```bash
make answer_dataset
```

**6. Evaluate retrieval quality** 📊
```bash
make evaluate
```

## 🏗️ System Architecture

```
Question
   │
   ▼
[Retriever — BM25s]
   │   ← BM25 index (data/processed/bm25_index/)
   │   ← Chunk metadata (data/processed/chunks/)
   │
   ▼
Top-k chunks (file_path + character indices)
   │
   ▼
[Generator — Qwen/Qwen3-0.6B via HF pipeline]
   │   ← Retrieved chunks injected into the prompt
   │
   ▼
Natural language answer (structured JSON output)
```

**Modules:**
- `indexer.py` — extracts the vLLM zip, walks the repo, chunks every file, builds and persists the BM25 index
- `chunker.py` — chunking strategies (AST-based for Python, paragraph/fixed-size for text)
- `retriever.py` — BM25 search over the index, single query and batch query
- `generator.py` — answer generation with Qwen3-0.6B through a HuggingFace `pipeline`
- `models.py` — Pydantic models for input/output validation
- `__main__.py` — CLI built with Python Fire

The retriever is a **singleton** 🔂: the BM25 index is built once during `index` and persisted to disk, then loaded into memory and reused across queries — it is never rebuilt per-question.

## ✂️ Chunking Strategy

Two strategies depending on file type:

- **Python files (`.py`)**: chunked using the `ast` module, splitting at function and class boundaries. This keeps each chunk semantically coherent (a chunk is never cut mid-function). If a single function/class exceeds `max_chunk_size`, it falls back to text chunking on that block.
- **Other files (`.md`, `.rst`, `.txt`)**: chunked by paragraph (`\n\n` boundaries), accumulating paragraphs until the size limit is reached. If a file has no paragraph breaks, it falls back to fixed-size chunking.

Default maximum chunk size: **2000 characters**, configurable via `--max_chunk_size`.

## 🧭 Retrieval Method

**BM25** via the `bm25s` library (chosen over the plain `bm25` package for its faster execution, lower memory footprint, and native save/load support — index, vocabulary, and scores are persisted as binary files instead of being recomputed every run).

BM25 ranks chunks using term frequency weighted by inverse document frequency: a word that appears often in a chunk but rarely across the whole corpus contributes more to that chunk's score than a common word. The index is an inverted table (word → which chunks contain it, with precomputed relevance scores), built once at indexing time and reused at query time without ever re-scanning the raw files.

## 📈 Performance Analysis

Measured on the public datasets (100 questions each):

| Dataset | Recall@1 | Recall@3 | Recall@5 | Recall@10 | Threshold (Recall@5) |
|---------|----------|----------|----------|-----------|------------------------|
| Docs    | 0.630    | 0.810    | **0.850** | 0.880     | ≥ 0.80 ✅ |
| Code    | 0.310    | 0.460    | **0.500** | 0.550     | ≥ 0.50 ✅ |

Both pass the minimum required thresholds 🎉. Docs retrieval performs notably better than code retrieval — natural-language documentation matches natural-language questions more directly with BM25's term-overlap scoring, while code questions often require matching identifiers/symbols against more verbose natural-language questions, which is inherently harder for a pure lexical method.

Indexing time, cold start, and warm throughput are all comfortably within the limits required by the subject (indexing in seconds, not minutes; batched search processes the full 100-question datasets in well under a second). ⚡

## 🧩 Design Decisions

- **BM25s over TF-IDF**: simpler to reason about (pure term-overlap ranking, no vector math to debug) and better suited to a technical corpus like source code.
- **AST-based chunking for Python**: functions and classes are natural semantic units; splitting elsewhere produces incomplete, hard-to-use chunks.
- **Pydantic models with `model_dump_json()`**: guarantees the output always matches the schema the moulinette expects, and makes the JSON human-readable when inspecting results manually.
- **Pickle for chunk metadata**: chunk metadata (`file_path`, start/end indices) is a simple Python structure that doesn't need a human-readable format, so pickle avoids the overhead of re-parsing JSON for tens of thousands of chunks at search time.
- **HuggingFace `pipeline` for generation**: abstracts away tokenization, device placement, and decoding, keeping `generator.py` focused on prompt construction rather than low-level model plumbing.
- **Singleton-style model/index loading**: both the BM25 retriever and the Qwen model are loaded once into memory and reused across calls, instead of being reloaded for every question.

## 🧗 Challenges Faced

The main difficulty wasn't a single bug but the number of new concepts to internalize at once: BM25's inverted-index internals, AST traversal for code-aware chunking, how recall@k is actually computed (character-overlap matching rather than exact chunk equality), and how to size a prompt so the model has enough context without exceeding its window.

The most delicate part was **tuning the boundary between giving the model enough context and letting it hallucinate** 🎭: too little context and the model invents plausible-sounding but wrong answers; too much (or irrelevant chunks) and it tends to drift from the actual source content. The final prompt explicitly instructs the model to answer *only* from the provided context, and the retrieved chunks are capped to a fixed character budget to keep the context focused and on-topic.

## 📚 Resources

- 📰 [RAG — Introduction (Stéphane Robert)](https://blog.stephane-robert.info/docs/developper/programmation/python/rag-introduction/)
- ✂️ [RAG — Chunking strategies (Stéphane Robert)](https://blog.stephane-robert.info/docs/developper/programmation/python/rag-chunking/)
- 📊 [What is Recall@k? (Milvus)](https://milvus.io/ai-quick-reference/what-is-recallatk)
- 🌳 [Abstract Syntax Tree in Python (Medium)](https://medium.com/@dev.aguillin/abstract-syntax-tree-python-85d39a53e86d)
- 🏆 [BM25 explained (Luigi's Box)](https://www.luigisbox.fr/glossaire-recherche/bm25/)
- 🗜️ [The Python `zipfile` module (Très Facile)](https://www.tresfacile.net/le-module-python-zipfile-des-archives-zip/)
- ⚡ [`bm25s` — GitHub repository](https://github.com/xhluca/bm25s)
- 🔂 [Singleton design pattern (docstring.fr)](https://www.docstring.fr/glossaire/singleton/)
- 🤗 [HuggingFace Transformers — Quicktour](https://huggingface.co/docs/transformers/fr/quicktour)
- 🔥 [Python Fire — GitHub repository](https://github.com/google/python-fire)
- 🔥 [Python Fire — Guide](https://google.github.io/python-fire/guide/)
- 🐙 [Reference implementation explored for inspiration](https://github.com/canarddu38/RAG-against-the-machine)
- 📄 [RAG paper — Lewis et al., 2020](https://arxiv.org/abs/2005.11401)
- 🐍 [Python `ast` module documentation](https://docs.python.org/3/library/ast.html)
- 🧪 [Pydantic documentation](https://docs.pydantic.dev/)

**AI usage** 🤝: AI was used to help understand the purpose of the topic, provide an overview of its overall structure, and clarify certain concepts.
It was also used to generate this ReadMe based on my own handwritten notes taken during this project 🧠
