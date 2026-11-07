"""
Embeddings and Semantic Vector Representation for Context Router.
Provides deterministic, zero-dependency subword n-gram vectorization with cosine similarity,
with pluggable support for neural embedding libraries when available.
"""

import math
import re
import struct
import hashlib
from typing import List, Tuple, Sequence

# Default embedding dimension (compatible with standard small transformer models)
VECTOR_DIM = 384

# Precompiled regex for splitting camelCase, snake_case, and standard word boundaries
TOKEN_SPLIT_REGEX = re.compile(r"[_\-\s\./\\,;:!?()[\]{}'\"`<>]+")
CAMEL_REGEX = re.compile(r"([a-z])([A-Z])")


def tokenize_text(text: str) -> List[str]:
    """
    Split text into normalized tokens, expanding camelCase and snake_case terms.
    """
    if not text:
        return []
    # Expand camelCase: e.g. "authMiddleware" -> "auth Middleware"
    text = CAMEL_REGEX.sub(r"\1 \2", text).lower()
    # Split on delimiters
    raw_tokens = TOKEN_SPLIT_REGEX.split(text)
    return [t for t in raw_tokens if len(t) > 1]


def extract_subwords_and_ngrams(tokens: List[str]) -> List[Tuple[str, float]]:
    """
    Generate tokens and subword character n-grams with appropriate weighting.
    """
    features: List[Tuple[str, float]] = []
    for token in tokens:
        # Full word feature
        features.append((f"w:{token}", 1.5))

        # Character n-grams for morphological prefix/suffix matching (lengths 3 to 5)
        t_len = len(token)
        if t_len >= 3:
            for n in (3, 4, 5):
                if t_len >= n:
                    for i in range(t_len - n + 1):
                        ngram = token[i : i + n]
                        # Give higher weight to prefix n-grams (e.g. ^auth)
                        weight = 1.0 if i == 0 else 0.6
                        features.append((f"ng:{ngram}", weight))
    return features


class BaseEmbeddingEngine:
    """Abstract base interface for embedding engines."""

    dimension: int = VECTOR_DIM

    def embed_text(self, text: str, title: str = "") -> List[float]:
        raise NotImplementedError

    def similarity(self, vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
        raise NotImplementedError


class DeterministicLocalEmbedder(BaseEmbeddingEngine):
    """
    Zero-dependency deterministic semantic vectorizer.
    Projects words, headers, and subword n-grams into a fixed L2-normalized dense space.
    Extremely fast (<1ms per document) and runs on vanilla Python standard library.
    """

    def __init__(self, dimension: int = VECTOR_DIM):
        self.dimension = dimension

    def _hash_feature(self, feature: str) -> Tuple[int, float]:
        """
        Hash feature to index [0, dimension) and sign {-1.0, 1.0}.
        """
        digest = hashlib.md5(feature.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], byteorder="little") % self.dimension
        sign = 1.0 if (digest[4] & 1) == 0 else -1.0
        return idx, sign

    def embed_text(self, text: str, title: str = "") -> List[float]:
        """
        Produce a dense unit-normalized embedding vector for given text and optional title.
        """
        vec = [0.0] * self.dimension

        # Process title with higher weight multiplier
        if title:
            title_tokens = tokenize_text(title)
            title_features = extract_subwords_and_ngrams(title_tokens)
            for feat, weight in title_features:
                idx, sign = self._hash_feature(feat)
                vec[idx] += sign * weight * 2.5

        # Process body content
        body_tokens = tokenize_text(text)
        body_features = extract_subwords_and_ngrams(body_tokens)
        for feat, weight in body_features:
            idx, sign = self._hash_feature(feat)
            vec[idx] += sign * weight

        # Apply logarithmic term dampening & L2 normalization
        norm_sq = 0.0
        for i in range(self.dimension):
            v = vec[i]
            if v != 0.0:
                # Damped activation
                v_damped = math.copysign(math.log1p(abs(v)), v)
                vec[i] = v_damped
                norm_sq += v_damped * v_damped

        if norm_sq > 0.0:
            norm = math.sqrt(norm_sq)
            for i in range(self.dimension):
                vec[i] /= norm

        return vec

    def similarity(self, vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
        """
        Compute cosine similarity between two unit-normalized vectors.
        Returns value clamped in [-1.0, 1.0].
        """
        if len(vec_a) != len(vec_b):
            raise ValueError(f"Vector length mismatch: {len(vec_a)} vs {len(vec_b)}")
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        return max(-1.0, min(1.0, dot))


def pack_vector(vec: Sequence[float]) -> bytes:
    """Pack float vector into binary bytes for compact SQLite BLOB storage."""
    return struct.pack(f"{len(vec)}f", *vec)


def unpack_vector(data: bytes, dim: int = VECTOR_DIM) -> List[float]:
    """Unpack binary bytes into float vector."""
    return list(struct.unpack(f"{dim}f", data))


def get_embedding_engine() -> BaseEmbeddingEngine:
    """
    Factory function returning the best available embedding engine.
    Gracefully falls back to DeterministicLocalEmbedder with 0 dependencies.
    """
    # Check for optional fastembed / sentence-transformers
    try:
        from fastembed import TextEmbedding  # type: ignore

        class FastEmbedEngine(BaseEmbeddingEngine):
            def __init__(self):
                self.model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
                self.dimension = 384

            def embed_text(self, text: str, title: str = "") -> List[float]:
                combined = f"{title}\n{text}" if title else text
                res = list(self.model.embed([combined]))
                return list(res[0])

            def similarity(self, vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
                dot = sum(a * b for a, b in zip(vec_a, vec_b))
                return max(-1.0, min(1.0, dot))

        return FastEmbedEngine()
    except ImportError:
        pass

    # Default to deterministic local embedder
    return DeterministicLocalEmbedder()
