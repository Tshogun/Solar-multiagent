"""
PDF RAG Agent
Handles PDF upload, processing, indexing, and retrieval
"""

from pathlib import Path
from typing import List, Dict, Any
import shutil

from backend.agents.base_agent import BaseAgent
from backend.models import AgentType, AgentResponse, DocumentChunk
from backend.utils.pdf_processor import PDFProcessor, validate_pdf
from backend.storage.vector_store import vector_store
from backend.config import settings


class PDFRAGAgent(BaseAgent):
    """Agent for PDF processing and retrieval-augmented generation"""
    
    def __init__(self):
        super().__init__(AgentType.PDF_RAG, "PDF RAG Agent")
        self.pdf_processor = PDFProcessor()
        self.vector_store = vector_store
        self.indexed_files = set()
    
    async def initialize(self) -> bool:
        """Initialize the PDF RAG agent"""
        try:
            # Load sample PDFs if available
            await self.index_sample_pdfs()
            
            self.initialized = True
            self.log_action("initialized", {"vector_store_stats": self.vector_store.get_stats()})
            return True
            
        except Exception as e:
            self.log_action("initialization_failed", {"error": str(e)})
            return False
    
    async def index_sample_pdfs(self):
        """Index sample PDFs from sample_pdfs directory"""
        sample_dir = settings.SAMPLE_PDFS_DIR
        
        if not sample_dir.exists():
            self.log_action("no_sample_pdfs", {"message": "Sample PDFs directory not found"})
            return
        
        pdf_files = list(sample_dir.glob("*.pdf"))
        
        if not pdf_files:
            self.log_action("no_sample_pdfs", {"message": "No PDFs found in sample directory"})
            return
        
        for pdf_file in pdf_files:
            if pdf_file.name not in self.indexed_files:
                try:
                    await self.index_pdf(pdf_file)
                    self.indexed_files.add(pdf_file.name)
                except Exception as e:
                    self.log_action("sample_pdf_index_failed", {
                        "file": pdf_file.name,
                        "error": str(e)
                    })
        
        self.log_action("sample_pdfs_indexed", {"count": len(self.indexed_files)})
    
    async def index_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Process and index a PDF file
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Dictionary with indexing results
        """
        # Validate PDF
        if not validate_pdf(pdf_path):
            raise ValueError(f"Invalid or unreadable PDF: {pdf_path}")
        
        # Process PDF
        chunks, metadata = self.pdf_processor.process_pdf(pdf_path)
        
        # Extract texts and metadata for indexing
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Add to vector store
        self.vector_store.add_documents(texts, metadatas)
        
        # Save vector store
        self.vector_store.save()
        
        result = {
            "filename": pdf_path.name,
            "num_pages": metadata["num_pages"],
            "num_chunks": len(chunks),
            "indexed": True
        }
        
        self.log_action("pdf_indexed", result)
        return result
    
    async def upload_and_index(self, file_path: Path, original_filename: str) -> Dict[str, Any]:
        """
        Handle PDF upload and indexing
        
        Args:
            file_path: Temporary path where file is saved
            original_filename: Original filename from upload
        
        Returns:
            Dictionary with upload results
        """
        try:
            # Move to uploads directory
            upload_path = settings.UPLOAD_DIR / original_filename
            shutil.move(str(file_path), str(upload_path))
            
            # Index the PDF
            result = await self.index_pdf(upload_path)
            result["file_path"] = str(upload_path)
            
            # Add to indexed files
            self.indexed_files.add(original_filename)
            
            return result
            
        except Exception as e:
            # Clean up on error
            if file_path.exists():
                file_path.unlink()
            raise e
    
    async def retrieve(self, query: str, top_k: int = None) -> List[DocumentChunk]:
        """
        Retrieve relevant document chunks for a query
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of DocumentChunk objects
        """
        top_k = top_k or settings.TOP_K_RETRIEVAL
        
        # Search vector store
        results = self.vector_store.search(query, top_k=top_k)
        
        # Convert to DocumentChunk objects
        chunks = []
        for result in results:
            chunk = DocumentChunk(
                content=result["content"],
                source=result["metadata"].get("filename", "unknown"),
                page=result["metadata"].get("page"),
                score=result["score"],
                metadata=result["metadata"]
            )
            chunks.append(chunk)
        
        self.log_action("retrieved_chunks", {"query": query, "num_results": len(chunks)})
        return chunks
    
    async def process(self, query: str, **kwargs) -> AgentResponse:
        """
        Process a RAG query
        
        Args:
            query: User query
            **kwargs: Additional parameters (top_k, etc.)
        
        Returns:
            AgentResponse with retrieved documents
        """
        try:
            top_k = kwargs.get("top_k", settings.TOP_K_RETRIEVAL)
            
            # Check if vector store has documents
            if self.vector_store.index is None or self.vector_store.index.ntotal == 0:
                return AgentResponse(
                    agent_type=self.agent_type,
                    success=False,
                    error="No documents indexed. Please upload PDFs first.",
                    retrieved_docs=[]
                )
            
            # Retrieve relevant chunks
            chunks = await self.retrieve(query, top_k=top_k)
            
            if not chunks:
                return AgentResponse(
                    agent_type=self.agent_type,
                    success=False,
                    error="No relevant documents found for the query.",
                    retrieved_docs=[]
                )
            
            # Prepare response data
            data = {
                "num_results": len(chunks),
                "top_score": chunks[0].score if chunks else 0.0,
                "sources": list(set(chunk.source for chunk in chunks))
            }
            
            return AgentResponse(
                agent_type=self.agent_type,
                success=True,
                data=data,
                retrieved_docs=chunks
            )
            
        except Exception as e:
            self.log_action("process_error", {"error": str(e)})
            return AgentResponse(
                agent_type=self.agent_type,
                success=False,
                error=str(e),
                retrieved_docs=[]
            )
    
    def get_indexed_files(self) -> List[str]:
        """Get list of indexed PDF files"""
        return list(self.indexed_files)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about indexed documents"""
        return {
            **self.vector_store.get_stats(),
            "indexed_files": len(self.indexed_files),
            "files": list(self.indexed_files)
        }


if __name__ == "__main__":
    import asyncio
    
    async def test_agent():
        agent = PDFRAGAgent()
        await agent.initialize()
        
        # Test retrieval
        response = await agent.execute("What is artificial intelligence?")
        print(f"Success: {response.success}")
        print(f"Retrieved docs: {len(response.retrieved_docs)}")
        
        if response.retrieved_docs:
            print("\nTop result:")
            print(f"Score: {response.retrieved_docs[0].score:.4f}")
            print(f"Content: {response.retrieved_docs[0].content[:200]}")
    
    asyncio.run(test_agent())