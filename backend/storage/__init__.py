# backend/storage/__init__.py
"""
Storage modules
"""

from .vector_store import FAISSVectorStore, vector_store

__all__ = [
    "FAISSVectorStore",
    "vector_store",
]
