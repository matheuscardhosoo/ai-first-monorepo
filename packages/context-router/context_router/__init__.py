"""
Context Router - Hybrid Discovery and Retrieval Engine for Distributed AGENTS.md files.
"""

from .api import search_context, get_topological_map, get_domain_context, build_index
from .engine import ContextSearchEngine
from .indexer import RepositoryContextScanner
from .embeddings import get_embedding_engine

__version__ = "1.0.0"
__all__ = [
    "search_context",
    "get_topological_map",
    "get_domain_context",
    "build_index",
    "ContextSearchEngine",
    "RepositoryContextScanner",
    "get_embedding_engine",
]
