# Solar Multi-Agent AI System

A modular multi-agent AI system that dynamically routes user queries to specialized agents for optimal information retrieval and synthesis.

## Features

- **Dynamic Routing**: LLM-powered controller automatically decides which agents to call
- **PDF RAG Agent**: Process and query uploaded PDF documents using vector search
- **Web Search Agent**: Real-time web search for current information
- **ArXiv Agent**: Search and retrieve academic papers
- **Answer Synthesis**: Intelligent combination of information from multiple sources
- **Comprehensive Logging**: Full traceability of decisions and agent interactions

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                       |
│                  (Streamlit Frontend)                   |
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                       |
├──────────────────────┬──────────────────────────────────┤
│                      │                                  |
│          ┌───────────▼────────────┐                     │
│          │   Controller Agent     │                     │
│          │  (LLM-based Routing)   │                     │
│          └───────────┬────────────┘                     │
│                      │                                  |
│        ┌─────────────┼─────────────┐                    |
│        │             │             │                    │
│   ┌────▼─────┐  ┌───▼────┐  ┌─────▼──────┐              |
│   │ PDF RAG  │  │  Web   │  │   ArXiv    │              |
│   │  Agent   │  │ Search │  │   Agent    │              |
│   │          │  │ Agent  │  │            │              |
│   └────┬─────┘  └───┬────┘  └─────┬──────┘              |
│        │            │             │                     |
│   ┌────▼─────┐  ┌───▼────┐  ┌─────▼──────┐              |
│   │  FAISS   │  │ DuckDGo│  │  ArXiv API │              |
│   │  Vector  │  │ Search │  │            │              |
│   │  Store   │  └────────┘  └────────────┘              |
│   └──────────┘                                          │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3+
- Groq API Key (https://console.groq.com)
- Serp API key
- Internet connection for web search and ArXiv

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd multi-agent-system
```

### 2. Create Virtual Environment

```bash
python -m venv venv
#on macos: source venv/bin/activate 
 # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY and SERP_API_KEY
```

### 5. Run the Backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

##  Project Structure

```
multi-agent-system/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── models.py               # Pydantic models
│   ├── agents/
│   │   ├── base_agent.py       # Base agent class
│   │   ├── controller.py       # Controller agent
│   │   ├── pdf_rag_agent.py    # PDF RAG agent
│   │   ├── web_search_agent.py # Web search agent
│   │   └── arxiv_agent.py      # ArXiv agent
│   ├── utils/
│   │   ├── pdf_processor.py    # PDF processing
│   │   ├── embeddings.py       # Embeddings
│   │   └── logger.py           # Logging
│   └── storage/
│       └── vector_store.py     # FAISS operations
├── frontend/
│   └── app.py                  # Streamlit UI
├── sample_pdfs/                # Sample PDFs
├── data/
│   ├── faiss_index/           # Vector store
│   └── uploads/               # Uploaded PDFs
├── logs/
│   └── agent_logs.json        # System logs
├── tests/                      # Unit tests
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Usage

### Query the System

1. Open the UI at `http://localhost:8000`
2. Enter your question in the text area
3. Click "Submit Query"
4. View the answer, agents used, and sources

**Example Queries:**
- "What are recent developments in large language models?"
- "Find papers about transformer architectures"
- "Summarize the uploaded PDF document"
- "What is the latest news about AI?"

### Upload PDF Documents

1. Navigate to "Upload PDF" page
2. Select a PDF file (max 10MB)
3. Click "Upload and Index"
4. The system will process and index the document

### View Logs and Statistics

- **Logs Page**: View recent queries and routing decisions
- **Statistics Page**: See system performance metrics

## API Endpoints

### Core Endpoints

- `GET /health` - Health check
- `POST /ask` - Submit a query
- `POST /upload_pdf` - Upload and index a PDF
- `GET /logs` - Get system logs
- `GET /stats` - Get statistics
- `GET /indexed_files` - List indexed PDFs

## Configuration

Edit `.env` file to customize:

```bash
# LLM Settings
LLM_MODEL=mixtral-8x7b-32768
LLM_TEMPERATURE=0.7
MAX_TOKENS=2048

# RAG Settings
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=5

# Search Settings
WEB_SEARCH_RESULTS=5
ARXIV_MAX_RESULTS=5
```

##  Running Tests

```bash
pytest
```

## Docker Deployment

Build Container: 
```bash
docker build -t multi-agent-system .
```
Run Container:
```bash
docker run -p 8000:8000 -p 8501:8501 \
  -e GROQ_API_KEY=your_key \
  multi-agent-system
```

## Deploy to Render

1. Push code to GitHub
2. Connect to Render
3. Add environment variables
4. Deploy!

See `render.yaml` for configuration.

## Security Considerations

- API keys stored in environment variables
- PDF uploads limited to 10MB
- File validation before processing
- No long-term storage of PII
- CORS configured for security

##  Monitoring

- All queries logged with timestamps
- Agent decisions tracked with rationale
- Execution times recorded
- Success rates monitored
