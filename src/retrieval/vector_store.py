import math
import sqlite3
import struct
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Optional

from src.ingestion.chunker import Chunk


class VectorStore:
    """A small persistent vector store backed by SQLite.

    Exact cosine search is fast enough for the few hundred transcript chunks a
    local YouTube workflow normally creates, and avoids platform-specific native
    vector-index crashes on Windows.
    """

    def __init__(self, persist_dir: str = "./data/vectors"):
        directory = Path(persist_dir).expanduser().resolve()
        directory.mkdir(parents=True, exist_ok=True)
        self.db_path = directory / "vectors.sqlite3"
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 30000")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    video_id TEXT NOT NULL,
                    video_url TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    document TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    embedding_dim INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_chunks_video_id
                    ON chunks(video_id);
                """
            )

    @staticmethod
    def _pack_embedding(embedding: List[float]) -> bytes:
        return struct.pack(f"<{len(embedding)}f", *embedding)

    @staticmethod
    def _unpack_embedding(data: bytes, dimension: int) -> tuple[float, ...]:
        return struct.unpack(f"<{dimension}f", data)

    @staticmethod
    def _cosine_similarity(left: List[float], right: tuple[float, ...]) -> float:
        if len(left) != len(right):
            raise ValueError(
                f"Embedding dimension mismatch: query has {len(left)}, stored vectors have {len(right)}"
            )
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        similarity = sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)
        return max(-1.0, min(1.0, similarity))

    def add_chunks(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("Each chunk must have exactly one embedding")
        if not chunks:
            return

        dimensions = {len(embedding) for embedding in embeddings}
        if 0 in dimensions or len(dimensions) != 1:
            raise ValueError("Embeddings must be non-empty and have matching dimensions")

        rows = [
            (
                f"{chunk.video_id}_{chunk.chunk_index}",
                chunk.video_id,
                chunk.video_url,
                chunk.start_time,
                chunk.chunk_index,
                chunk.text,
                self._pack_embedding(embedding),
                len(embedding),
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO chunks (
                    id, video_id, video_url, start_time, chunk_index,
                    document, embedding, embedding_dim
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    video_id = excluded.video_id,
                    video_url = excluded.video_url,
                    start_time = excluded.start_time,
                    chunk_index = excluded.chunk_index,
                    document = excluded.document,
                    embedding = excluded.embedding,
                    embedding_dim = excluded.embedding_dim
                """,
                rows,
            )

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        video_ids: Optional[List[str]] = None,
    ) -> dict:
        if not query_embedding:
            raise ValueError("Query embedding must not be empty")
        if top_k <= 0:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        sql = "SELECT * FROM chunks"
        params: list[str] = []
        if video_ids:
            placeholders = ", ".join("?" for _ in video_ids)
            sql += f" WHERE video_id IN ({placeholders})"
            params.extend(video_ids)

        with self._connect() as connection:
            rows = connection.execute(sql, params).fetchall()

        ranked = []
        for row in rows:
            embedding = self._unpack_embedding(row["embedding"], row["embedding_dim"])
            similarity = self._cosine_similarity(query_embedding, embedding)
            ranked.append((similarity, row))
        ranked.sort(key=lambda item: item[0], reverse=True)

        selected = ranked[:top_k]
        return {
            "documents": [[row["document"] for _, row in selected]],
            "metadatas": [[
                {
                    "video_id": row["video_id"],
                    "video_url": row["video_url"],
                    "start_time": row["start_time"],
                    "chunk_index": row["chunk_index"],
                }
                for _, row in selected
            ]],
            "distances": [[1.0 - similarity for similarity, _ in selected]],
        }

    def get_indexed_videos(self) -> List[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT video_id, video_url
                FROM chunks
                GROUP BY video_id, video_url
                ORDER BY video_id
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_stats(self) -> dict:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT video_id, video_url, COUNT(*) AS chunks
                FROM chunks
                GROUP BY video_id, video_url
                ORDER BY video_id
                """
            ).fetchall()
        videos = [dict(row) for row in rows]
        return {
            "total_videos": len(videos),
            "total_chunks": sum(video["chunks"] for video in videos),
            "videos": videos,
        }

    def delete_video(self, video_id: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM chunks WHERE video_id = ?", (video_id,))
