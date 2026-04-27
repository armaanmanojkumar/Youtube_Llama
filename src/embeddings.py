from typing import List

_model = None
_model_name = None


def embed_texts(texts: List[str], model_name: str = "BAAI/bge-small-en-v1.5") -> List[List[float]]:
    global _model, _model_name
    from fastembed import TextEmbedding

    if _model is None or _model_name != model_name:
        _model = TextEmbedding(model_name=model_name)
        _model_name = model_name

    return [e.tolist() for e in _model.embed(texts)]
