import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.email_models import EmailClassificationRequest

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check and status endpoints."""
    
    def test_health_check(self):
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
        assert "ai_model_loaded" in data
    
    def test_status_endpoint(self):
        """Test detailed status endpoint."""
        response = client.get("/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "application" in data
        assert "ai_model" in data
        assert "processing" in data
        assert "configuration" in data


class TestClassificationEndpoints:
    """Test email classification endpoints."""
    
    def test_classify_productive_email(self):
        """Test classification of a productive email."""
        productive_email = {
            "content": "Prezados, estou com um problema no sistema e preciso de ajuda urgente para resolver. O relatório não está sendo gerado corretamente.",
            "source": "text_input"
        }
        
        response = client.post("/classify", json=productive_email)
        assert response.status_code == 200
        
        data = response.json()
        assert "category" in data
        assert "confidence" in data
        assert "suggested_response" in data
        assert "processing_time" in data
        assert "timestamp" in data
        
        # Check that confidence is within expected range
        assert 0.0 <= data["confidence"] <= 1.0
    
    def test_classify_unproductive_email(self):
        """Test classification of an unproductive email."""
        unproductive_email = {
            "content": "Oi pessoal! Espero que todos estejam bem. Queria agradecer pela festa de ontem, foi incrível! Abraços para todos.",
            "source": "text_input"
        }
        
        response = client.post("/classify", json=unproductive_email)
        assert response.status_code == 200
        
        data = response.json()
        assert "category" in data
        assert "confidence" in data
        assert "suggested_response" in data
        assert "processing_time" in data
        assert "timestamp" in data
        
        # Check that confidence is within expected range
        assert 0.0 <= data["confidence"] <= 1.0
    
    def test_classify_empty_content(self):
        """Test classification with empty content should fail."""
        empty_email = {
            "content": "",
            "source": "text_input"
        }
        
        response = client.post("/classify", json=empty_email)
        assert response.status_code == 422  # Validation error
    
    def test_classify_too_short_content(self):
        """Test classification with content too short."""
        short_email = {
            "content": "Hi",
            "source": "text_input"
        }
        
        response = client.post("/classify", json=short_email)
        assert response.status_code == 422  # Validation error
    
    def test_classify_too_long_content(self):
        """Test classification with content too long."""
        long_content = "A" * 10001  # Exceeds max length
        long_email = {
            "content": long_content,
            "source": "text_input"
        }
        
        response = client.post("/classify", json=long_email)
        assert response.status_code == 422  # Validation error


class TestFileUploadEndpoints:
    """Test file upload and processing endpoints."""
    
    def test_upload_txt_file(self):
        """Test uploading a text file."""
        test_content = b"Prezados, preciso de ajuda com um problema no sistema. E urgente!"
        
        response = client.post(
            "/upload",
            files={"file": ("test_email.txt", test_content, "text/plain")}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "filename" in data
        assert "file_size" in data
        assert "content_preview" in data
        assert "extraction_success" in data
        assert data["extraction_success"] is True
    
    def test_upload_unsupported_file(self):
        """Test uploading an unsupported file type."""
        test_content = b"Some content"
        
        response = client.post(
            "/upload",
            files={"file": ("test.doc", test_content, "application/msword")}
        )
        
        assert response.status_code == 400  # Bad request
    
    def test_upload_no_file(self):
        """Test upload endpoint without providing a file."""
        response = client.post("/upload")
        assert response.status_code == 422  # Validation error


class TestMetricsEndpoints:
    """Test metrics and monitoring endpoints."""
    
    def test_get_metrics(self):
        """Test getting processing metrics."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_processed" in data
        assert "productive_count" in data
        assert "unproductive_count" in data
        assert "average_confidence" in data
        assert "average_processing_time" in data
        assert "last_updated" in data
    
    def test_reset_metrics(self):
        """Test resetting processing metrics."""
        response = client.post("/metrics/reset")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data


class TestBatchProcessing:
    """Test batch classification functionality."""
    
    def test_batch_classify_multiple_emails(self):
        """Test batch classification of multiple emails."""
        emails = [
            {
                "content": "Preciso de ajuda com um problema técnico urgente no sistema.",
                "source": "text_input"
            },
            {
                "content": "Obrigado pela festa de aniversário, foi muito legal!",
                "source": "text_input"
            }
        ]
        
        response = client.post("/classify/batch", json=emails)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Check that all results have required fields
        for result in data:
            assert "category" in result
            assert "confidence" in result
            assert "suggested_response" in result
            assert "processing_time" in result
            assert "timestamp" in result
    
    def test_batch_classify_empty_list(self):
        """Test batch classification with empty list."""
        response = client.post("/classify/batch", json=[])
        assert response.status_code == 400  # Bad request
    
    def test_batch_classify_too_many_emails(self):
        """Test batch classification with too many emails."""
        # Create a list with more than 50 emails (the limit)
        emails = [
            {
                "content": f"Test email number {i}. This is a test message.",
                "source": "text_input"
            }
            for i in range(51)
        ]
        
        response = client.post("/classify/batch", json=emails)
        assert response.status_code == 400  # Bad request


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])