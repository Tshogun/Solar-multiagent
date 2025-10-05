"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AgentType(str, Enum):
    """Types of agents in the system"""
    CONTROLLER = "controller"
    PDF_RAG = "pdf_rag"
    WEB_SEARCH = "web_search"
    ARXIV = "arxiv"


class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    query: str = Field(..., min_length=1, max_length=2000, description="User query")
    use_rag: bool = Field(default=True, description="Whether to use RAG if available")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are recent developments in transformer models?",
                "use_rag": True
            }
        }


class DocumentChunk(BaseModel):
    """Represents a retrieved document chunk"""
    content: str
    source: str
    page: Optional[int] = None
    score: Optional[float] = None
    metadata: Dict[str, Any] = {}


class AgentDecision(BaseModel):
    """Controller's decision about which agents to call"""
    agents_to_call: List[AgentType]
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentResponse(BaseModel):
    """Response from an individual agent"""
    agent_type: AgentType
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    retrieved_docs: List[DocumentChunk] = []
    execution_time: float = 0.0


class QueryResponse(BaseModel):
    """Final response to user query"""
    query: str
    answer: str
    agents_used: List[AgentType]
    decision_rationale: str
    sources: List[DocumentChunk] = []
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is GPT?",
                "answer": "GPT (Generative Pre-trained Transformer) is...",
                "agents_used": ["pdf_rag", "web_search"],
                "decision_rationale": "Used RAG for existing knowledge and web search for recent updates",
                "sources": [],
                "execution_time": 2.5,
                "timestamp": "2025-01-01T12:00:00"
            }
        }


class PDFUploadResponse(BaseModel):
    """Response after PDF upload"""
    filename: str
    file_size: int
    num_pages: int
    num_chunks: int
    indexed: bool
    message: str


class LogEntry(BaseModel):
    """Log entry for controller decisions"""
    request_id: str
    timestamp: datetime
    query: str
    decision: AgentDecision
    agents_responses: List[AgentResponse]
    final_answer: str
    total_execution_time: float


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    services: Dict[str, bool] = {}
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-01-01T12:00:00",
                "services": {
                    "groq_api": True,
                    "faiss_index": True,
                    "pdf_processor": True
                }
            }
        }