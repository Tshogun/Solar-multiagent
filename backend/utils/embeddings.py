from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
from pathlib import Path

from backend.config import settings


class EmbeddingModel:
    """Wrapper for embedding model operations"""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        """Singleton pattern to avoid loading model multiple times"""
        if cls._instance is None:
            cls._instance = super(EmbeddingModel, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self.load_model()
    
    def load_model(self):
        """Load the sentence transformer model"""
        try:
            print(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            print(f"✓ Model loaded successfully")
            print(f"  - Embedding dimension: {self._model.get_sentence_embedding_dimension()}")
        except Exception as e:
            raise Exception(f"Failed to load embedding model: {str(e)}")
    
    def encode(
        self, 
        texts: Union[str, List[str]], 
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Generate embeddings for text(s)
        
        Args:
            texts: Single text or list of texts
            batch_size: Batch size for encoding
            show_progress: Show progress bar
        
        Returns:
            Numpy array of embeddings
        """
        if self._model is None:
            self.load_model()
        
        # Convert single text to list
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            return embeddings
        except Exception as e:
            raise Exception(f"Encoding failed: {str(e)}")
    
    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode a single query (optimized for search)
        
        Args:
            query: Query text
        
        Returns:
            Embedding vector as numpy array
        """
        return self.encode(query)[0]
    
    def encode_documents(self, documents: List[str], show_progress: bool = True) -> np.ndarray:
        """
        Encode multiple documents (optimized for indexing)
        
        Args:
            documents: List of document texts
            show_progress: Show progress bar
        
        Returns:
            Numpy array of embeddings
        """
        return self.encode(documents, batch_size=32, show_progress=show_progress)
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        if self._model is None:
            self.load_model()
        return self._model.get_sentence_embedding_dimension()
    
    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        
        Returns:
            Similarity score (0-1)
        """
        # Normalize vectors
        embedding1_norm = embedding1 / np.linalg.norm(embedding1)
        embedding2_norm = embedding2 / np.linalg.norm(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1_norm, embedding2_norm)
        
        return float(similarity)


# Global instance
embedding_model = EmbeddingModel()


# Helper functions
def embed_text(text: str) -> np.ndarray:
    """Quick function to embed single text"""
    return embedding_model.encode_query(text)


def embed_texts(texts: List[str]) -> np.ndarray:
    """Quick function to embed multiple texts"""
    return embedding_model.encode_documents(texts)


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts"""
    emb1 = embed_text(text1)
    emb2 = embed_text(text2)
    return embedding_model.cosine_similarity(emb1, emb2)


if __name__ == "__main__":
    # Test embeddings
    model = EmbeddingModel()
    
    # Test single text
    text = "This is a test sentence."
    embedding = model.encode_query(text)
    print(f"Embedding shape: {embedding.shape}")
    print(f"Embedding dimension: {model.get_dimension()}")
    
    # Test multiple texts
    texts = [
        "Artificial intelligence is transforming the world.",
        "Machine learning is a subset of AI.",
        "Deep learning uses neural networks."
    ]
    embeddings = model.encode_documents(texts)
    print(f"Batch embeddings shape: {embeddings.shape}")
    
    # Test similarity
    sim = calculate_similarity(texts[0], texts[1])
    print(f"Similarity between first two texts: {sim:.4f}")