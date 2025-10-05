# Multi-Agent AI System

A modular multi-agent AI system that dynamically routes user queries to specialized agents for optimal information retrieval and synthesis.

## 🌟 Features

- **Dynamic Routing**: LLM-powered controller automatically decides which agents to call
- **PDF RAG Agent**: Process and query uploaded PDF documents using vector search
- **Web Search Agent**: Real-time web search for current information
- **ArXiv Agent**: Search and retrieve academic papers
- **Answer Synthesis**: Intelligent combination of information from multiple sources
- **Comprehensive Logging**: Full traceability of decisions and agent interactions
- **Modern UI**: Clean Streamlit interface for easy interaction

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│                  (Streamlit Frontend)                    │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
├──────────────────────┬──────────────────────────────────┤
│                      │                                   │
│          ┌───────────▼────────────┐                     │
│          │   Controller Agent     │                     │
│          │  (LLM-based Routing)   │                     │
│          └───────────┬────────────┘                     │
│                      │                                   │
│        ┌─────────────┼─────────────┐                   │
│        │             │             │                    │
│   ┌────▼─────┐  ┌───▼────┐  ┌─────▼──────┐            │
│   │ PDF RAG  │  │  Web   │  │   ArXiv    │            │
│   │  Agent   │  │ Search │  │   Agent    │            │
│   │          │  │ Agent  │  │            │            │
│   └────┬─────┘  └───┬────┘  └─────┬──────┘            │
│        │            │             │                     │
│   ┌────▼─────┐  ┌───▼────┐  ┌─────▼──────┐            │
│   │  FAISS   │  │ DuckDGo│  │  ArXiv API │            │
│   │  Vector  │  │ Search │  │            │            │
│   │  Store   │  └────────┘  └────────────┘            │
│   └──────────┘                                          │
└─────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- Python 3.9+
- Groq API Key ([Get one here](https://console.groq.com))
- 2GB+ RAM for embeddings model
- Internet connection for web search and ArXiv

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd multi-agent-system
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 5. Run the Backend

```bash
cd backend
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

### 6. Run the Frontend (New Terminal)

```bash
streamlit run frontend/app.py
```

The UI will open at `http://localhost:8501`

## 📁 Project Structure

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

## 🎯 Usage

### Query the System

1. Open the Streamlit UI at `http://localhost:8501`
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

## 🔧 API Endpoints

### Core Endpoints

- `GET /health` - Health check
- `POST /ask` - Submit a query
- `POST /upload_pdf` - Upload and index a PDF
- `GET /logs` - Get system logs
- `GET /stats` - Get statistics
- `GET /indexed_files` - List indexed PDFs

### Example API Usage

```bash
# Query the system
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?"}'

# Upload a PDF
curl -X POST "http://localhost:8000/upload_pdf" \
  -F "file=@document.pdf"

# Get logs
curl "http://localhost:8000/logs?limit=10"
```

## ⚙️ Configuration

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

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend tests/

# Run specific test file
pytest tests/test_agents.py
```

## 🐳 Docker Deployment

```bash
# Build image
docker build -t multi-agent-system .

# Run container
docker run -p 8000:8000 -p 8501:8501 \
  -e GROQ_API_KEY=your_key \
  multi-agent-system
```

## 🌐 Deploy to Render

1. Push code to GitHub
2. Connect to Render
3. Add environment variables
4. Deploy!

See `deployment/render.yaml` for configuration.

## 🔒 Security Considerations

- API keys stored in environment variables
- PDF uploads limited to 10MB
- File validation before processing
- No long-term storage of PII
- CORS configured for security

## 📊 Monitoring

- All queries logged with timestamps
- Agent decisions tracked with rationale
- Execution times recorded
- Success rates monitored

## 🐛 Troubleshooting

### Backend won't start
- Check if `.env` file exists with `GROQ_API_KEY`
- Ensure port 8000 is not in use
- Verify all dependencies installed

### PDF upload fails
- Check file size (max 10MB)
- Ensure PDF is not corrupted
- Verify upload directory permissions

### No search results
- Check internet connection
- Verify API keys
- Check if documents are indexed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

MIT License - See LICENSE file for details

## 👥 Authors

NebulaByte Development Team

## 🙏 Acknowledgments

- Groq for LLM API
- Sentence Transformers for embeddings
- FAISS for vector search
- FastAPI and Streamlit for frameworks

## 📮 Support

For issues and questions:
- Open an issue on GitHub
- Contact: support@nebulabyte.com

---

**Note**: This project is for educational purposes as part of the NebulaByte internship program.