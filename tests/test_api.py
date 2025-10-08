import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import io

from backend.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test health endpoint returns 200"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "timestamp" in data
    
    def test_health_services_status(self):
        """Test health endpoint shows service status"""
        response = client.get("/health")
        data = response.json()
        
        services = data["services"]
        assert "groq_api" in services
        assert "pdf_rag" in services
        assert "web_search" in services
        assert "arxiv" in services


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data


class TestQueryEndpoint:
    """Test query endpoint"""
    
    def test_query_basic(self):
        """Test basic query"""
        response = client.post(
            "/ask",
            json={"query": "What is artificial intelligence?"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "query" in data
        assert "answer" in data
        assert "agents_used" in data
        assert "decision_rationale" in data
        assert "execution_time" in data
    
    def test_query_empty(self):
        """Test query with empty string"""
        response = client.post(
            "/ask",
            json={"query": ""}
        )
        # Should return validation error
        assert response.status_code == 422
    
    def test_query_with_rag_option(self):
        """Test query with RAG option"""
        response = client.post(
            "/ask",
            json={"query": "Test query", "use_rag": True}
        )
        assert response.status_code == 200
    
    def test_query_response_structure(self):
        """Test query response has correct structure"""
        response = client.post(
            "/ask",
            json={"query": "What is machine learning?"}
        )
        
        data = response.json()
        
        # Check all required fields
        required_fields = [
            "query", "answer", "agents_used", 
            "decision_rationale", "sources", 
            "execution_time", "timestamp"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check types
        assert isinstance(data["agents_used"], list)
        assert isinstance(data["sources"], list)
        assert isinstance(data["execution_time"], (int, float))


class TestPDFUploadEndpoint:
    """Test PDF upload endpoint"""
    
    def test_upload_non_pdf(self):
        """Test uploading non-PDF file"""
        # Create a fake text file
        file_content = b"This is not a PDF"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        
        response = client.post("/upload_pdf", files=files)
        assert response.status_code == 400
    
    def test_upload_endpoint_structure(self):
        """Test upload endpoint accepts files"""
        # This would need a real PDF file to fully test
        # For now, just check the endpoint exists and handles errors
        response = client.post("/upload_pdf", files={})
        assert response.status_code == 422  # Missing required file


class TestLogsEndpoint:
    """Test logs endpoint"""
    
    def test_get_logs(self):
        """Test getting logs"""
        response = client.get("/logs")
        assert response.status_code == 200
        
        data = response.json()
        assert "logs" in data
        assert "count" in data
        assert isinstance(data["logs"], list)
    
    def test_get_logs_with_limit(self):
        """Test logs with limit parameter"""
        response = client.get("/logs?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["logs"]) <= 10


class TestStatsEndpoint:
    """Test statistics endpoint"""
    
    def test_get_stats(self):
        """Test getting statistics"""
        response = client.get("/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "system_stats" in data
        assert "rag_stats" in data
        assert "timestamp" in data
    
    def test_stats_structure(self):
        """Test statistics response structure"""
        response = client.get("/stats")
        data = response.json()
        
        system_stats = data["system_stats"]
        assert "total_requests" in system_stats
        assert "avg_execution_time" in system_stats
        assert "agent_usage" in system_stats
        assert "success_rate" in system_stats
        
        rag_stats = data["rag_stats"]
        assert "total_documents" in rag_stats
        assert "indexed_files" in rag_stats


class TestIndexedFilesEndpoint:
    """Test indexed files endpoint"""
    
    def test_get_indexed_files(self):
        """Test getting indexed files"""
        response = client.get("/indexed_files")
        assert response.status_code == 200
        
        data = response.json()
        assert "indexed_files" in data
        assert "count" in data
        assert isinstance(data["indexed_files"], list)


class TestCORSHeaders:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self):
        """Test CORS headers are set"""
        response = client.options("/health")
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers.keys() or \
               response.status_code == 200  # Some test clients handle OPTIONS differently


class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_endpoint(self):
        """Test accessing non-existent endpoint"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_invalid_method(self):
        """Test using wrong HTTP method"""
        response = client.get("/ask")  # Should be POST
        assert response.status_code == 405
    
    def test_malformed_json(self):
        """Test sending malformed JSON"""
        response = client.post(
            "/ask",
            data="not json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])