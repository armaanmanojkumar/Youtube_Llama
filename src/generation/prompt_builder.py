from typing import List


def build_context(chunks: List[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk["metadata"]
        url = meta.get("video_url", "")
        start = int(meta.get("start_time", 0))
        timestamp_url = f"{url}&t={start}" if "youtube" in url else url
        parts.append(f"[Source {i}] {timestamp_url}\n{chunk['document']}")
    return "\n\n---\n\n".join(parts)


def build_prompt(query: str, chunks: List[dict]) -> list:
    context = build_context(chunks)
    return [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that answers questions based on YouTube video transcripts. "
                "Cite sources using [Source N] notation. "
                "If the context does not contain enough information, say so clearly."
            ),
        },
        {
            "role": "user",
            "content": f"Context:\n\n{context}\n\nQuestion: {query}",
        },
    ]
