import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path
from typing import List, Dict, Any, Tuple
import re

from backend.config import settings


class PDFProcessor:
    """Extract and process text from PDF files"""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    
    def extract_text_pymupdf(self, pdf_path: Path) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from PDF using PyMuPDF
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Tuple of (full_text, metadata)
        """
        try:
            doc = fitz.open(pdf_path)
            text_parts = []
            metadata = {
                "filename": pdf_path.name,
                "num_pages": len(doc),
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
            }
            
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text()
                if text.strip():
                    text_parts.append(f"[Page {page_num}]\n{text}")
            
            doc.close()
            full_text = "\n\n".join(text_parts)
            
            return full_text, metadata
            
        except Exception as e:
            raise Exception(f"PyMuPDF extraction failed: {str(e)}")
    
    def extract_text_pdfplumber(self, pdf_path: Path) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from PDF using pdfplumber (fallback method)
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Tuple of (full_text, metadata)
        """
        try:
            text_parts = []
            
            with pdfplumber.open(pdf_path) as pdf:
                metadata = {
                    "filename": pdf_path.name,
                    "num_pages": len(pdf.pages),
                    "title": pdf.metadata.get("Title", ""),
                    "author": pdf.metadata.get("Author", ""),
                }
                
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if text and text.strip():
                        text_parts.append(f"[Page {page_num}]\n{text}")
            
            full_text = "\n\n".join(text_parts)
            return full_text, metadata
            
        except Exception as e:
            raise Exception(f"pdfplumber extraction failed: {str(e)}")
    
    def extract_text(self, pdf_path: Path) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from PDF with fallback methods
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Tuple of (full_text, metadata)
        """
        try:
            return self.extract_text_pymupdf(pdf_path)
        except Exception as e1:
            print(f"PyMuPDF failed, trying pdfplumber: {e1}")
            try:
                return self.extract_text_pdfplumber(pdf_path)
            except Exception as e2:
                raise Exception(f"All extraction methods failed. PyMuPDF: {e1}, pdfplumber: {e2}")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:()\[\]-]', '', text)
        # Normalize line breaks
        text = text.replace('\n', ' ').strip()
        
        return text
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Full text to chunk
            metadata: Optional metadata to attach to each chunk
        
        Returns:
            List of chunk dictionaries with content and metadata
        """
        # Clean text first
        text = self.clean_text(text)
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Define chunk end
            end = start + self.chunk_size
            
            # If not at the end, try to break at sentence boundary
            if end < text_length:
                # Look for sentence ending punctuation
                sentence_end = max(
                    text.rfind('. ', start, end),
                    text.rfind('! ', start, end),
                    text.rfind('? ', start, end)
                )
                
                if sentence_end != -1 and sentence_end > start:
                    end = sentence_end + 1
            
            # Extract chunk
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk_data = {
                    "content": chunk_text,
                    "chunk_id": len(chunks),
                    "start_char": start,
                    "end_char": end,
                    "metadata": metadata or {}
                }
                chunks.append(chunk_data)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
        
        return chunks
    
    def process_pdf(self, pdf_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Complete PDF processing: extract, clean, and chunk
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Tuple of (chunks_list, pdf_metadata)
        """
        # Extract text and metadata
        full_text, metadata = self.extract_text(pdf_path)
        
        # Add file path to metadata
        metadata["file_path"] = str(pdf_path)
        
        # Chunk the text
        chunks = self.chunk_text(full_text, metadata)
        
        print(f"Processed {pdf_path.name}: {len(chunks)} chunks from {metadata['num_pages']} pages")
        
        return chunks, metadata


# Utility functions
def validate_pdf(file_path: Path) -> bool:
    """Validate if file is a readable PDF"""
    if not file_path.exists():
        return False
    
    if file_path.suffix.lower() not in settings.ALLOWED_EXTENSIONS:
        return False
    
    if file_path.stat().st_size > settings.MAX_UPLOAD_SIZE:
        return False
    
    try:
        with fitz.open(file_path) as doc:
            return len(doc) > 0
    except:
        return False


if __name__ == "__main__":
    # Test PDF processor
    processor = PDFProcessor()
    test_pdf = Path("sample_pdfs/placeholder.pdf")
    
    if test_pdf.exists():
        chunks, metadata = processor.process_pdf(test_pdf)
        print(f"Extracted {len(chunks)} chunks")
        print(f"Metadata: {metadata}")