# YouTube RAG — Local AI-Powered Video Search

Query any YouTube video using natural language, powered entirely by local LLMs via Ollama. No API keys. No cloud. Full privacy.

---

## What it does

Paste a YouTube URL → the transcript is fetched, chunked, and embedded into a local vector database (ChromaDB). Ask any question about the video and get a cited, context-grounded answer from your chosen local model.

---

## Tech stack

| Layer | Technology |
|---|---|
| LLM inference | Ollama (`gemma3:e4b`, `llama3.1:latest`) |
| Embeddings | Ollama (`nomic-embed-text`) |
| Vector database | ChromaDB (persistent, on-disk) |
| Backend | FastAPI (Python 3.11+) |
| Frontend | React + Vite + TypeScript |
| Transcript fetch | `youtube-transcript-api` + `yt-dlp` |

---

## Project structure

```
youtube-rag/
├── src/
│   ├── ingestion/
│   │   ├── youtube_fetcher.py     # Transcript fetch via youtube-transcript-api
│   │   ├── chunker.py             # Sliding window chunking with overlap
│   │   └── embedder.py            # Calls Ollama /api/embeddings
│   ├── retrieval/
│   │   ├── vector_store.py        # ChromaDB CRUD and collections
│   │   └── retriever.py           # Cosine similarity, top-k, MMR
│   ├── generation/
│   │   ├── prompt_builder.py      # Context injection and system prompt
│   │   └── ollama_client.py       # Chat + embedding endpoints, streaming
│   └── api/
│       ├── main.py                # FastAPI app init, CORS, lifespan
│       └── routes/
│           ├── ingest.py          # POST /ingest · DELETE /video
│           └── query.py           # POST /query · GET /videos
├── frontend/
│   ├── src/
│   │   ├── components/            # VideoCard, ChatWindow, SourceChip
│   │   ├── hooks/                 # useIngest, useQuery, useOllama
│   │   └── api/
│   │       └── client.ts          # Typed fetch wrapper for backend
│   ├── index.html
│   └── vite.config.ts
├── data/
│   ├── chroma/                    # Vector DB on disk (gitignored)
│   └── transcripts/               # Raw JSON per video (gitignored)
├── tests/
│   ├── test_ingestion.py
│   └── test_retrieval.py
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Prerequisites

- [Ollama](https://ollama.com) installed and running
- Python 3.11+
- Node.js 18+

Pull the required models before starting:

```bash
ollama pull gemma3:e4b
ollama pull llama3.1:latest
ollama pull nomic-embed-text
```

Enable CORS so the browser can talk to Ollama directly (required for the frontend):

```bash
OLLAMA_ORIGINS="*" ollama serve
```

To set this permanently, add `export OLLAMA_ORIGINS="*"` to your shell profile (`~/.zshrc` or `~/.bashrc`).

---

## Getting started

### 1. Clone and configure

```bash
git clone https://github.com/your-org/youtube-rag.git
cd youtube-rag
cp .env.example .env
```

Edit `.env` with your settings:

```env
OLLAMA_HOST=http://localhost:11434
MODEL=gemma3:e4b
EMBED_MODEL=nomic-embed-text
CHUNK_SIZE=400
CHUNK_OVERLAP=50
TOP_K=4
```

### 2. Backend setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload --port 8000
```

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173`. The backend API is at `http://localhost:8000`.

### 4. Docker (alternative)

```bash
docker-compose up --build
```

This starts Ollama, the FastAPI backend, and the Vite frontend together.

---

## API reference

### `POST /ingest`

Index a YouTube video by URL.

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

Response:

```json
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Video title",
  "chunks_indexed": 42,
  "status": "indexed"
}
```

### `POST /query`

Query across all indexed videos.

```json
{
  "query": "What did they say about the main topic?",
  "top_k": 4
}
```

Response:

```json
{
  "answer": "Based on the transcript...",
  "sources": [
    {
      "video_id": "dQw4w9WgXcQ",
      "title": "Video title",
      "chunk": "...relevant passage...",
      "score": 0.87
    }
  ]
}
```

### `GET /videos`

List all indexed videos.

### `DELETE /video/{video_id}`

Remove a video and all its chunks from the vector store.

---

## RAG pipeline

```
YouTube URL
    │
    ▼
youtube_fetcher.py       ← fetches transcript via youtube-transcript-api
    │
    ▼
chunker.py               ← sliding window, configurable size + overlap
    │
    ▼
embedder.py              ← calls Ollama nomic-embed-text per chunk
    │
    ▼
vector_store.py          ← stores vectors + metadata in ChromaDB
    │
    ▼  (at query time)
retriever.py             ← cosine similarity, top-k + optional MMR
    │
    ▼
prompt_builder.py        ← injects retrieved chunks as context
    │
    ▼
ollama_client.py         ← streams answer from gemma3:e4b or llama3.1
```

---

## Hyperparameters

All tunable via `.env` or passed directly to the API:

| Parameter | Default | Description |
|---|---|---|
| `MODEL` | `gemma3:e4b` | Chat model used for generation |
| `EMBED_MODEL` | `nomic-embed-text` | Embedding model for chunks and queries |
| `CHUNK_SIZE` | `400` | Characters per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between adjacent chunks |
| `TOP_K` | `4` | Number of chunks retrieved per query |
| `temperature` | `0.2` | Generation temperature (lower = more factual) |

For factual RAG queries, keep `temperature` between `0.1` and `0.3`. For exploratory or creative queries, raise it to `0.7`.

---

## Team and branch ownership

| Branch | Owner | Scope |
|---|---|---|
| `feat/ingestion` | Person 1 | `src/ingestion/`, `tests/test_ingestion.py` |
| `feat/retrieval` | Person 2 | `src/retrieval/`, `data/chroma/`, `tests/test_retrieval.py` |
| `feat/api` | Person 3 | `src/api/`, `src/generation/` |
| `feat/frontend` | Person 4 | `frontend/` |

All branches merge into `main` via pull request. Direct pushes to `main` are disabled. See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full workflow.

**Merge order:** `feat/ingestion` → `feat/retrieval` → `feat/api` → `feat/frontend`

---

## Running tests

```bash
pytest tests/ -v
```
