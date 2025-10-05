"""
FAISS Vector Store
Handles vector indexing and similarity search
"""

import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple
import json

from backend.config import settings
from backend.utils.embeddings import embedding_model


class FAISSVectorStore:
    """FAISS-based vector store for semantic search"""
    
    def __init__(self, index_path: Path = None):
        self.index_path = index_path or settings.FAISS_INDEX_PATH
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.index_path / "faiss.index"
        self.metadata_file = self.index_path / "metadata.pkl"
        
        self.index = None
        self.documents = []  # Store document metadata
        self.dimension = embedding_model.get_dimension()
        
        # Load existing index if available
        self.load()
    
    def create_index(self):
        """Create a new FAISS index"""
        # Using IndexFlatL2 for exact search (can upgrade to IndexIVFFlat for speed)
        self.index = faiss.IndexFlatL2(self.dimension)
        print(f"✓ Created new FAISS index with dimension {self.dimension}")
    
    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]] = None):
        """
        Add documents to the vector store
        
        Args:
            texts: List of text chunks to add
            metadatas: Optional list of metadata dicts for each text
        """
        if self.index is None:
            self.create_index()
        
        if not texts:
            return
        
        # Generate embeddings
        print(f"Generating embeddings for {len(texts)} documents...")
        embeddings = embedding_model.encode_documents(texts, show_progress=True)
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        
        # Store metadata
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        for text, metadata in zip(texts, metadatas):
            doc_entry = {
                "content": text,
                "metadata": metadata,
                "doc_id": len(self.documents)
            }
            self.documents.append(doc_entry)
        
        print(f"✓ Added {len(texts)} documents to index")
        print(f"  Total documents in index: {len(self.documents)}")
    
    def search(
        self, 
        query: str, 
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Query text
            top_k: Number of results to return
        
        Returns:
            List of documents with scores
        """
        if self.index is None or self.index.ntotal == 0:
            return []
        
        top_k = top_k or settings.TOP_K_RETRIEVAL
        
        # Generate query embedding
        query_embedding = embedding_model.encode_query(query)
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        
        # Search
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        # Prepare results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                # Convert L2 distance to similarity score (0-1)
                doc["score"] = float(1 / (1 + dist))
                doc["distance"] = float(dist)
                results.append(doc)
        
        return results
    
    def save(self):
        """Save index and metadata to disk"""
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_file))
            
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self.documents, f)
            
            print(f"✓ Saved index to {self.index_file}")
            print(f"  Documents: {len(self.documents)}")
    
    def load(self):
        """Load index and metadata from disk"""
        if self.index_file.exists() and self.metadata_file.exists():
            try:
                self.index = faiss.read_index(str(self.index_file))
                
                with open(self.metadata_file, 'rb') as f:
                    self.documents = pickle.load(f)
                
                print(f"✓ Loaded existing index from {self.index_file}")
                print(f"  Documents: {len(self.documents)}")
                return True
            except Exception as e:
                print(f"Failed to load index: {e}")
                self.create_index()
                return False
        else:
            self.create_index()
            return False
    
    def clear(self):
        """Clear the index and metadata"""
        self.create_index()
        self.documents = []
        print("✓ Cleared vector store")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        return {
            "total_documents": len(self.documents),
            "index_size": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "index_path": str(self.index_path)
        }
    
    def delete_by_source(self, source: str):
        """Delete documents by source filename"""
        # Note: FAISS doesn't support deletion easily
        # We need to rebuild the index without those documents
        filtered_docs = [doc for doc in self.documents if doc.get("metadata", {}).get("filename") != source]
        
        if len(filtered_docs) < len(self.documents):
            # Rebuild index
            self.clear()
            texts = [doc["content"] for doc in filtered_docs]
            metadatas = [doc["metadata"] for doc in filtered_docs]
            
            if texts:
                self.add_documents(texts, metadatas)
            
            print(f"✓ Deleted documents from source: {source}")


# Global vector store instance
vector_store = FAISSVectorStore()


if __name__ == "__main__":
    # Test vector store
    store = FAISSVectorStore()
    
    # Add test documents
    test_docs = [
        "Artificial intelligence is revolutionizing technology.",
        "Machine learning models require large datasets.",
        "Deep learning uses neural networks with many layers.",
        "Natural language processing helps computers understand text."
    ]
    
    test_metadata = [
        {"source": "test", "topic": "AI"},
        {"source": "test", "topic": "ML"},
        {"source": "test", "topic": "DL"},
        {"source": "test", "topic": "NLP"}
    ]
    
    store.add_documents(test_docs, test_metadata)
    
    # Test search
    results = store.search("What is deep learning?", top_k=3)
    print("\nSearch results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result['score']:.4f}")
        print(f"   Content: {result['content'][:100]}")
    
    # Save
    store.save()
    
    print("\nStats:", store.get_stats())