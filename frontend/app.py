"""
Streamlit Frontend for Multi-Agent AI System
Simple and intuitive UI for querying and PDF upload
"""

import streamlit as st
import requests
from datetime import datetime
import json

# Configure page
st.set_page_config(
    page_title="Multi-Agent AI System",
    page_icon="🤖",
    layout="wide"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .agent-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        margin: 0.2rem;
        border-radius: 15px;
        font-size: 0.9rem;
        font-weight: bold;
    }
    .badge-pdf {
        background-color: #ff7f0e;
        color: white;
    }
    .badge-web {
        background-color: #2ca02c;
        color: white;
    }
    .badge-arxiv {
        background-color: #d62728;
        color: white;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)


def check_backend_health():
    """Check if backend is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def query_backend(query: str):
    """Send query to backend"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/ask",
            json={"query": query, "use_rag": True},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. The query is taking too long.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error: {str(e)}")
        return None


def upload_pdf(file):
    """Upload PDF to backend"""
    try:
        files = {"file": (file.name, file, "application/pdf")}
        response = requests.post(
            f"{API_BASE_URL}/upload_pdf",
            files=files,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Upload failed: {str(e)}")
        return None


def get_logs(limit=20):
    """Get system logs"""
    try:
        response = requests.get(f"{API_BASE_URL}/logs?limit={limit}", timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None


def get_stats():
    """Get system statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None


def get_indexed_files():
    """Get list of indexed files"""
    try:
        response = requests.get(f"{API_BASE_URL}/indexed_files", timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None


def display_agent_badge(agent_type: str):
    """Display colored badge for agent type"""
    badge_class = {
        "pdf_rag": "badge-pdf",
        "web_search": "badge-web",
        "arxiv": "badge-arxiv"
    }.get(agent_type, "badge-pdf")
    
    agent_name = {
        "pdf_rag": "📄 PDF RAG",
        "web_search": "🌐 Web Search",
        "arxiv": "📚 ArXiv"
    }.get(agent_type, agent_type)
    
    return f'<span class="agent-badge {badge_class}">{agent_name}</span>'


# Main App
def main():
    # Header
    st.markdown('<div class="main-header">🤖 Multi-Agent AI System</div>', unsafe_allow_html=True)
    
    # Check backend health
    if not check_backend_health():
        st.error("❌ Backend is not running. Please start the FastAPI server first.")
        st.code("cd backend && uvicorn main:app --reload", language="bash")
        return
    
    st.success("✅ Backend is running")
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Navigation")
        page = st.radio(
            "Select Page:",
            ["🔍 Query System", "📤 Upload PDF", "📊 System Logs", "📈 Statistics"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Show indexed files
        st.subheader("📁 Indexed Files")
        indexed_data = get_indexed_files()
        if indexed_data and indexed_data.get("indexed_files"):
            for file in indexed_data["indexed_files"]:
                st.text(f"✓ {file}")
        else:
            st.text("No files indexed yet")
    
    # Main Content
    if page == "🔍 Query System":
        show_query_page()
    elif page == "📤 Upload PDF":
        show_upload_page()
    elif page == "📊 System Logs":
        show_logs_page()
    elif page == "📈 Statistics":
        show_stats_page()


def show_query_page():
    """Query interface page"""
    st.header("🔍 Query the Multi-Agent System")
    
    st.markdown("""
    Ask any question and the system will automatically route it to the appropriate agents:
    - **PDF RAG**: For questions about uploaded documents
    - **Web Search**: For recent information and news
    - **ArXiv**: For academic papers and research
    """)
    
    # Example queries
    with st.expander("💡 Example Queries"):
        examples = [
            "What are recent developments in large language models?",
            "Find papers about transformer architectures",
            "Summarize the uploaded PDF document",
            "What is the latest news about AI?",
            "Explain machine learning concepts"
        ]
        for example in examples:
            if st.button(example, key=example):
                st.session_state.query = example
    
    # Query input
    query = st.text_area(
        "Enter your query:",
        height=100,
        placeholder="Type your question here...",
        value=st.session_state.get("query", "")
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        submit = st.button("🚀 Submit Query", type="primary", use_container_width=True)
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.query = ""
            st.rerun()
    
    if submit and query:
        with st.spinner("🤔 Processing your query..."):
            result = query_backend(query)
        
        if result:
            # Display answer
            st.markdown("### 💬 Answer")
            st.markdown(result.get("answer", "No answer generated"))
            
            # Display agents used
            st.markdown("### 🤖 Agents Used")
            agents_html = " ".join([
                display_agent_badge(agent) 
                for agent in result.get("agents_used", [])
            ])
            st.markdown(agents_html, unsafe_allow_html=True)
            
            # Display decision rationale
            st.markdown("### 🧠 Decision Rationale")
            st.info(result.get("decision_rationale", "No rationale provided"))
            
            # Display sources
            sources = result.get("sources", [])
            if sources:
                st.markdown("### 📚 Sources")
                for i, source in enumerate(sources[:5], 1):
                    with st.expander(f"Source {i}: {source.get('source', 'Unknown')[:50]}..."):
                        st.markdown(f"**Score:** {source.get('score', 0):.4f}")
                        st.markdown(f"**Content:**\n{source.get('content', '')[:500]}...")
                        if source.get('metadata'):
                            st.json(source['metadata'])
            
            # Display execution time
            st.caption(f"⏱️ Execution time: {result.get('execution_time', 0):.2f}s")


def show_upload_page():
    """PDF upload page"""
    st.header("📤 Upload PDF Documents")
    
    st.markdown("""
    Upload PDF files to add them to the knowledge base. The system will:
    1. Extract text from the PDF
    2. Split it into chunks
    3. Generate embeddings
    4. Index it in the vector store
    """)
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Upload a PDF document (max 10MB)"
    )
    
    if uploaded_file:
        st.info(f"📄 Selected: {uploaded_file.name} ({uploaded_file.size / 1024:.2f} KB)")
        
        if st.button("📥 Upload and Index", type="primary"):
            with st.spinner("Processing PDF..."):
                result = upload_pdf(uploaded_file)
            
            if result:
                st.success("✅ PDF uploaded and indexed successfully!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Pages", result.get("num_pages", 0))
                with col2:
                    st.metric("Chunks", result.get("num_chunks", 0))
                with col3:
                    st.metric("Size", f"{result.get('file_size', 0) / 1024:.2f} KB")
                
                st.info(result.get("message", ""))
                st.balloons()


def show_logs_page():
    """System logs page"""
    st.header("📊 System Logs")
    
    st.markdown("View recent queries and agent interactions")
    
    limit = st.slider("Number of logs to display", 5, 100, 20)
    
    if st.button("🔄 Refresh Logs"):
        st.rerun()
    
    logs_data = get_logs(limit)
    
    if logs_data and logs_data.get("logs"):
        logs = logs_data["logs"]
        st.info(f"Showing {len(logs)} most recent logs")
        
        for log in reversed(logs):
            with st.expander(
                f"🕐 {log.get('timestamp', 'N/A')} - {log.get('query', 'No query')[:60]}..."
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("**Query:**")
                    st.text(log.get("query", "N/A"))
                    
                    st.markdown("**Decision:**")
                    decision = log.get("decision", {})
                    agents_html = " ".join([
                        display_agent_badge(agent) 
                        for agent in decision.get("agents_called", [])
                    ])
                    st.markdown(agents_html, unsafe_allow_html=True)
                    st.caption(decision.get("rationale", "N/A"))
                
                with col2:
                    st.metric("Execution Time", f"{log.get('total_execution_time', 0):.2f}s")
                    st.metric("Confidence", f"{decision.get('confidence', 0):.2f}")
                
                # Agent responses
                st.markdown("**Agent Responses:**")
                for resp in log.get("agent_responses", []):
                    status = "✅" if resp.get("success") else "❌"
                    st.text(
                        f"{status} {resp.get('agent_type', 'N/A')} - "
                        f"{resp.get('num_retrieved_docs', 0)} docs - "
                        f"{resp.get('execution_time', 0):.2f}s"
                    )
    else:
        st.warning("No logs available")


def show_stats_page():
    """Statistics page"""
    st.header("📈 System Statistics")
    
    if st.button("🔄 Refresh Stats"):
        st.rerun()
    
    stats = get_stats()
    
    if stats:
        # System stats
        st.subheader("🔧 System Performance")
        system_stats = stats.get("system_stats", {})
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Requests", system_stats.get("total_requests", 0))
        with col2:
            st.metric("Avg Execution Time", f"{system_stats.get('avg_execution_time', 0):.2f}s")
        with col3:
            st.metric("Success Rate", f"{system_stats.get('success_rate', 0):.1f}%")
        with col4:
            agent_usage = system_stats.get("agent_usage", {})
            st.metric("Most Used Agent", max(agent_usage, key=agent_usage.get) if agent_usage else "N/A")
        
        # Agent usage chart
        st.subheader("🤖 Agent Usage")
        agent_usage = system_stats.get("agent_usage", {})
        if agent_usage:
            st.bar_chart(agent_usage)
        else:
            st.info("No usage data yet")
        
        # RAG stats
        st.subheader("📚 Knowledge Base (RAG)")
        rag_stats = stats.get("rag_stats", {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Documents", rag_stats.get("total_documents", 0))
        with col2:
            st.metric("Indexed Files", rag_stats.get("indexed_files", 0))
        with col3:
            st.metric("Embedding Dimension", rag_stats.get("dimension", 0))
        
        # Indexed files list
        if rag_stats.get("files"):
            st.markdown("**Indexed Files:**")
            for file in rag_stats["files"]:
                st.text(f"✓ {file}")
    else:
        st.error("Failed to load statistics")


if __name__ == "__main__":
    main()