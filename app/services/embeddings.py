from __future__ import annotations
import os
import time
from typing import List
import numpy as np
from openai import OpenAI

from app.config import settings

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=60.0)
    return _client


def embed_texts(
    texts: List[str],
    model: str = None,
    batch_size: int = 64,
    max_retries: int = 5
) -> np.ndarray:
    """
    Generate embeddings for a list of texts using OpenAI API.
    
    Args:
        texts: List of text strings to embed
        model: Model name (defaults to settings.OPENAI_EMBED_MODEL)
        batch_size: Number of texts to process in one API call
        max_retries: Maximum retry attempts for failed requests
        
    Returns:
        numpy array of shape (len(texts), EMBED_DIM) with L2-normalized embeddings
    """
    if model is None:
        model = settings.OPENAI_EMBED_MODEL
    
    # Sanitize inputs
    texts = [t if (t and str(t).strip()) else "" for t in texts]
    out = np.zeros((len(texts), settings.EMBED_DIM), dtype=np.float32)
    client = _get_client()
    
    def _call_api(batch: List[str], attempt: int):
        resp = client.embeddings.create(model=model, input=batch)
        vecs = [np.array(d.embedding, dtype=np.float32) for d in resp.data]
        return np.vstack(vecs)
    
    i = 0
    while i < len(texts):
        batch = texts[i:i + batch_size]
        
        for attempt in range(1, max_retries + 1):
            try:
                arr = _call_api(batch, attempt)
                # L2 normalize for cosine similarity
                norms = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-9
                arr = (arr / norms).astype(np.float32)
                out[i:i + len(batch)] = arr
                break
            except Exception as e:
                if attempt == max_retries:
                    raise RuntimeError(f"Embedding failed after {max_retries} attempts: {e}")
                # Exponential backoff
                sleep_s = min(2 ** attempt, 30)
                print(f"Embedding attempt {attempt} failed, retrying in {sleep_s}s...")
                time.sleep(sleep_s)
        
        i += len(batch)
    
    return out


def embed_single(text: str, model: str = None) -> np.ndarray:
    """Convenience function to embed a single text"""
    return embed_texts([text], model=model)[0]
