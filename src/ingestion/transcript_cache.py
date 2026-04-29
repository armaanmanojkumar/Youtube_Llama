import json
from pathlib import Path
from typing import Dict, List, Optional


class TranscriptCache:
    def __init__(self, cache_dir: str = "./data/transcripts"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _file_path(self, video_id: str) -> Path:
        return self.cache_dir / f"{video_id}.json"

    def load(self, video_id: str) -> Optional[Dict[str, object]]:
        path = self._file_path(video_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, video_id: str, transcript: List[dict], metadata: Dict[str, object]) -> None:
        path = self._file_path(video_id)
        path.write_text(
            json.dumps({"transcript": transcript, "metadata": metadata}, indent=2),
            encoding="utf-8",
        )
