# YouTube LLaMA Studio

A polished local video search experience powered by Ollama, ChromaDB, and YouTube transcript intelligence.

This repository now includes a streamlined backend, transcript caching, metadata fallback, and a lightweight animated web interface served directly from the API.

## What it does

- Ingests YouTube videos by URL
- Fetches transcripts with a fallback to `yt-dlp` captions
- Chunks and embeds transcript text into ChromaDB
- Answers questions with evidence, timestamps, and citations
- Shows indexed videos, performance metrics, and model selection
- Serves a responsive animated UI at `/`

## Tech stack

| Layer | Technology |
|---|---|
| LLM inference | Ollama |
| Embeddings | Ollama (`nomic-embed-text`) |
| Vector database | ChromaDB |
| Backend | FastAPI |
| UI | Static HTML/CSS/JS served by FastAPI |
| Transcript fetch | `youtube-transcript-api`, `yt-dlp`, `httpx` |

## Project structure

```
Youtube_Llama-main/
├── frontend/
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── src/
│   ├── api/
│   │   ├── main.py
│   │   └── routes/
│   │       ├── ingest.py
│   │       └── query.py
│   ├── generation/
│   │   ├── ollama_client.py
│   │   └── prompt_builder.py
│   ├── ingestion/
│   │   ├── chunker.py
│   │   ├── embedder.py
│   │   ├── transcript_cache.py
│   │   └── youtube_fetcher.py
│   └── retrieval/
│       ├── retriever.py
│       └── vector_store.py
├── data/
│   ├── chroma/
│   └── transcripts/
├── Dockerfile.backend
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Prerequisites

- [Ollama](https://ollama.com) installed and running
- Python 3.11+

Pull the required models before using the app:

```bash
ollama pull llama3.1:latest
ollama pull nomic-embed-text
```

## Local development

### 1. Backend only

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload --port 8000
```

Open `http://localhost:8000` after startup.

### 2. Docker

```bash
docker-compose up --build
```

The interface is available at `http://localhost:8000`.

## Configuration

Copy `.env.example` to `.env` and update values as needed.

Example:

```env
OLLAMA_HOST=http://localhost:11434
MODEL=llama3.1:latest
EMBED_MODEL=nomic-embed-text
CHUNK_SIZE=450
CHUNK_OVERLAP=100
TOP_K=4
ALLOW_ORIGINS=*
```

## API endpoints

- `POST /ingest` — ingest a YouTube video
- `POST /query` — ask a question across indexed transcripts
- `GET /videos` — list indexed video IDs and URLs
- `GET /stats` — corpus statistics
- `GET /models` — available Ollama models
- `GET /performance` — recent query performance
- `GET /health` — health check

## Notes

- Transcripts are cached in `data/transcripts`
- Vector embeddings are persisted in `data/chroma`
- The UI is served from `/static` and `/`
- The app is designed for local/offline use with Ollama
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
