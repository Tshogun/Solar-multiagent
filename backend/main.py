from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import time
from datetime import datetime
from typing import List
import shutil

from backend.config import settings, initialize_directories, validate_settings
from backend.models import (
    QueryRequest, QueryResponse, PDFUploadResponse, 
    HealthResponse, AgentType, DocumentChunk
)
from backend.agents.controller import ControllerAgent
from backend.agents.pdf_rag_agent import PDFRAGAgent
from backend.agents.web_search_agent import WebSearchAgent
from backend.agents.arxiv_agent import ArXivAgent
from backend.utils.logger import logger
from backend.storage.vector_store import vector_store
from groq import Groq
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("=" * 50)
    print("Starting Multi-Agent AI System")
    print("=" * 50)
    
    try:
        validate_settings()
        await controller.initialize()
        #await pdf_rag.initialize()
        await web_search.initialize()
        await arxiv_agent.initialize()
        print("\n✓ All agents initialized successfully")
        print(f"✓ Server running on {settings.HOST}:{settings.PORT}")
        print("=" * 50)
    except Exception as e:
        print(f"\n✗ Initialization failed: {e}")
        raise
    
    yield
    
    # Shutdown (if needed)
    print("Shutting down...")

# Initialize directories
initialize_directories()

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent AI System",
    description="Dynamic multi-agent system with PDF RAG, Web Search, and ArXiv agents",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend static files
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

# Initialize agents
controller = ControllerAgent()
pdf_rag = PDFRAGAgent()
web_search = WebSearchAgent()
arxiv_agent = ArXivAgent()

# Groq client for answer synthesis
groq_client = Groq(api_key=settings.GROQ_API_KEY)

async def synthesize_answer(
    query: str,
    agent_responses: List,
    decision_rationale: str
) -> str:
    """
    Synthesize final answer from agent responses using LLM
    
    Args:
        query: User query
        agent_responses: List of agent responses
        decision_rationale: Why these agents were chosen
    f
    Returns:
        Synthesized answer
    """
    # Collect all retrieved information
    context_parts = []
    
    for response in agent_responses:
        if response.success and response.retrieved_docs:
            agent_name = response.agent_type.value
            context_parts.append(f"\n=== Information from {agent_name.upper()} ===")
            
            for i, doc in enumerate(response.retrieved_docs[:3], 1):
                context_parts.append(f"\n[Source {i}]")
                context_parts.append(doc.content[:800])  # Limit content length
                context_parts.append(f"(Source: {doc.source})")
    
    if not context_parts:
        return "I couldn't find relevant information to answer your query. Please try rephrasing or upload relevant documents."
    
    context = "\n".join(context_parts)
    
    # Create synthesis prompt
    prompt = f"""You are an AI assistant that synthesizes information from multiple sources to answer user queries.

User Query: {query}

Routing Decision: {decision_rationale}

Retrieved Information:
{context}

Instructions:
1. Synthesize a comprehensive answer based on the retrieved information
2. Be concise and direct
3. Cite sources when making specific claims (e.g., "According to [source]...")
4. If information is conflicting, acknowledge it
5. If information is insufficient, state what's missing

Provide your answer:"""
    
    try:
        response = groq_client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.MAX_TOKENS
        )
        
        answer = response.choices[0].message.content.strip()
        return answer
        
    except Exception as e:
        print(f"Error synthesizing answer: {e}")
        # Fallback: return concatenated information
        return f"Based on the retrieved information:\n\n{context[:1000]}"


@app.get("/", response_class=FileResponse)
async def serve_frontend():
    """Serve the HTML frontend"""
    frontend_file = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_file.exists():
        return FileResponse(frontend_file)
    return {"message": "Multi-Agent AI System API", "version": "1.0.0", "docs": "/docs"}


@app.get("/api", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "message": "Multi-Agent AI System API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "query": "/ask",
            "upload": "/upload_pdf",
            "logs": "/logs",
            "stats": "/stats"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services = {
        "groq_api": controller.initialized,
        "pdf_rag": pdf_rag.initialized,
        "web_search": web_search.initialized,
        "arxiv": arxiv_agent.initialized,
        "faiss_index": vector_store.index is not None
    }
    
    status = "healthy" if all(services.values()) else "degraded"
    
    return HealthResponse(
        status=status,
        timestamp=datetime.now(),
        services=services
    )


@app.post("/ask", response_model=QueryResponse)
async def ask_query(request: QueryRequest):
    """
    Process a user query through the multi-agent system
    
    Args:
        request: QueryRequest with query string
    
    Returns:
        QueryResponse with answer and metadata
    """
    start_time = time.time()
    
    try:
        query = request.query
        
        # Check if RAG has indexed documents
        has_indexed_docs = vector_store.index is not None and vector_store.index.ntotal > 0
        
        # Step 1: Controller decides which agents to call
        controller_response = await controller.execute(
            query,
            has_indexed_docs=has_indexed_docs,
            use_llm=True
        )
        
        if not controller_response.success:
            raise HTTPException(status_code=500, detail="Controller failed to route query")
        
        decision_data = controller_response.data
        agents_to_call = [AgentType(a) for a in decision_data["agents_to_call"]]
        decision_rationale = decision_data["rationale"]
        
        # Step 2: Call selected agents
        agent_responses = []
        
        for agent_type in agents_to_call:
            if agent_type == AgentType.PDF_RAG:
                response = await pdf_rag.execute(query, top_k=settings.TOP_K_RETRIEVAL)
            elif agent_type == AgentType.WEB_SEARCH:
                response = await web_search.execute(query)
            elif agent_type == AgentType.ARXIV:
                response = await arxiv_agent.execute(query)
            else:
                continue
            
            agent_responses.append(response)
        
        # Step 3: Synthesize final answer
        final_answer = await synthesize_answer(query, agent_responses, decision_rationale)
        
        # Step 4: Collect all sources
        all_sources = []
        for response in agent_responses:
            if response.success:
                all_sources.extend(response.retrieved_docs)
        
        # Step 5: Prepare response
        execution_time = time.time() - start_time
        
        query_response = QueryResponse(
            query=query,
            answer=final_answer,
            agents_used=agents_to_call,
            decision_rationale=decision_rationale,
            sources=all_sources[:10],  # Limit to top 10 sources
            execution_time=execution_time,
            timestamp=datetime.now()
        )
        
        # Step 6: Log the request
        from backend.models import AgentDecision
        decision = AgentDecision(
            agents_to_call=agents_to_call,
            rationale=decision_rationale,
            confidence=decision_data.get("confidence", 0.8)
        )
        
        logger.log_request(
            query=query,
            decision=decision,
            agent_responses=agent_responses,
            final_answer=final_answer,
            total_execution_time=execution_time
        )
        
        return query_response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@app.post("/upload_pdf", response_model=PDFUploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and index a PDF file
    
    Args:
        file: PDF file upload
    
    Returns:
        PDFUploadResponse with upload details
    """
    try:
        # Validate file
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Check file size
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB"
            )
        
        # Save temporary file
        temp_path = settings.UPLOAD_DIR / f"temp_{file.filename}"
        with open(temp_path, 'wb') as f:
            f.write(contents)
        
        # Process and index
        result = await pdf_rag.upload_and_index(temp_path, file.filename)
        
        return PDFUploadResponse(
            filename=result["filename"],
            file_size=file_size,
            num_pages=result["num_pages"],
            num_chunks=result["num_chunks"],
            indexed=result["indexed"],
            message=f"Successfully indexed {result['num_chunks']} chunks from {result['num_pages']} pages"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF upload failed: {str(e)}")


@app.get("/logs")
async def get_logs(limit: int = 50):
    """
    Get recent system logs
    
    Args:
        limit: Number of logs to return
    
    Returns:
        List of log entries
    """
    try:
        logs = logger.get_logs(limit=limit)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve logs: {str(e)}")


@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        log_stats = logger.get_stats()
        rag_stats = pdf_rag.get_stats()
        
        return {
            "system_stats": log_stats,
            "rag_stats": rag_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats: {str(e)}")


@app.get("/indexed_files")
async def get_indexed_files():
    """Get list of indexed PDF files"""
    try:
        files = pdf_rag.get_indexed_files()
        return {"indexed_files": files, "count": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve files: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )