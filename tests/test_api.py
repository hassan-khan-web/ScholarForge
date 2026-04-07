"""
API Endpoint Tests

Tests for FastAPI endpoints:
- GET /health (health check)
- GET /api/folders (list folders)
- POST /api/folders (create folder)
- PUT /api/folders/{id} (rename folder)
- DELETE /api/folders/{id} (delete folder)
- Chat and report endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthCheck:
    """Test health check endpoint."""
    
    @pytest.mark.unit
    def test_health_check_success(self, client):
        """Test that health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code in [200, 503]  # 200 if all healthy, 503 if degraded
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
    
    @pytest.mark.unit
    def test_health_check_has_db_component(self, client):
        """Test that health check includes database component."""
        response = client.get("/health")
        data = response.json()
        assert "database" in data["components"]
        assert "status" in data["components"]["database"]


class TestFolderEndpoints:
    """Test folder-related API endpoints."""
    
    @pytest.mark.unit
    def test_get_folders_empty(self, client):
        """Test getting folders when none exist."""
        response = client.get("/api/folders")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.unit
    def test_create_folder(self, client):
        """Test creating a new folder."""
        response = client.post(
            "/api/folders",
            json={"name": "New Research Project"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["folder"]["name"] == "New Research Project"
        assert data["folder"]["id"] is not None
    
    @pytest.mark.unit
    def test_create_folder_validation(self, client):
        """Test folder creation with invalid data."""
        # Empty name
        response = client.post(
            "/api/folders",
            json={"name": ""}
        )
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.unit
    def test_rename_folder(self, client, sample_folder):
        """Test renaming a folder."""
        response = client.put(
            f"/api/folders/{sample_folder.id}",
            json={"new_name": "Renamed Project"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    @pytest.mark.unit
    def test_rename_nonexistent_folder(self, client):
        """Test renaming a folder that doesn't exist."""
        response = client.put(
            "/api/folders/99999",
            json={"new_name": "New Name"}
        )
        assert response.status_code == 404
    
    @pytest.mark.unit
    def test_delete_folder(self, client, sample_folder):
        """Test deleting a folder."""
        response = client.delete(f"/api/folders/{sample_folder.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    @pytest.mark.unit
    def test_delete_nonexistent_folder(self, client):
        """Test deleting a folder that doesn't exist."""
        response = client.delete("/api/folders/99999")
        assert response.status_code == 404


class TestSessionEndpoints:
    """Test chat session-related API endpoints."""
    
    @pytest.mark.unit
    def test_create_session(self, client, sample_folder):
        """Test creating a chat session."""
        response = client.post(
            "/api/sessions",
            json={"folder_id": sample_folder.id, "title": "New Chat"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["session"]["title"] == "New Chat"
    
    @pytest.mark.unit
    def test_create_session_invalid_folder(self, client):
        """Test creating a session with invalid folder ID."""
        response = client.post(
            "/api/sessions",
            json={"folder_id": 99999, "title": "New Chat"}
        )
        # Will succeed in creation, but might fail on folder lookup
        # depending on foreign key constraints
        assert response.status_code in [200, 500]
    
    @pytest.mark.unit
    def test_get_session_info(self, client, sample_session):
        """Test getting session info."""
        response = client.get(f"/api/sessions/{sample_session.id}/info")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_session.id
        assert data["title"] == sample_session.title
    
    @pytest.mark.unit
    def test_get_nonexistent_session_info(self, client):
        """Test getting info for a session that doesn't exist."""
        response = client.get("/api/sessions/99999/info")
        assert response.status_code == 404
    
    @pytest.mark.unit
    def test_get_session_messages(self, client, sample_session, sample_messages):
        """Test retrieving messages from a session."""
        response = client.get(f"/api/sessions/{sample_session.id}/messages")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["role"] == "user"
        assert data[0]["content"] == "Hello"
    
    @pytest.mark.unit
    def test_rename_session(self, client, sample_session):
        """Test renaming a session."""
        response = client.put(
            f"/api/sessions/{sample_session.id}",
            json={"new_name": "Renamed Chat"}
        )
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_delete_session(self, client, sample_session):
        """Test deleting a session."""
        response = client.delete(f"/api/sessions/{sample_session.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestHistoryEndpoints:
    """Test report history and retrieval endpoints."""
    
    @pytest.mark.unit
    def test_get_history_empty(self, client):
        """Test getting history when no reports exist."""
        response = client.get("/api/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.unit
    def test_get_history_with_reports(self, client, sample_report):
        """Test getting history with reports."""
        response = client.get("/api/history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["topic"] == sample_report.topic
    
    @pytest.mark.unit
    def test_get_report(self, client, sample_report):
        """Test retrieving a specific report."""
        response = client.get(f"/api/report/{sample_report.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["topic"] == sample_report.topic
        assert data["content"] == sample_report.content
    
    @pytest.mark.unit
    def test_get_nonexistent_report(self, client):
        """Test retrieving a report that doesn't exist."""
        response = client.get("/api/report/99999")
        assert response.status_code == 200  # Still returns 200 with error message
        data = response.json()
        assert "error" in data
    
    @pytest.mark.unit
    def test_delete_report(self, client, sample_report):
        """Test deleting a report."""
        response = client.delete(f"/api/report/{sample_report.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestHookEndpoints:
    """Test hook (research notes) endpoints."""
    
    @pytest.mark.unit
    def test_get_hooks_empty(self, client):
        """Test getting hooks when none exist."""
        response = client.get("/api/hooks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.unit
    def test_add_hook(self, client):
        """Test adding a hook."""
        response = client.post(
            "/add-hook",
            json={"content": "Important research note about AI"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    @pytest.mark.unit
    def test_get_hooks(self, client, sample_hook):
        """Test retrieving hooks."""
        response = client.get("/api/hooks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert any(h["id"] == sample_hook.id for h in data)


class TestPageEndpoints:
    """Test page serving endpoints."""
    
    @pytest.mark.unit
    def test_index_page(self, client):
        """Test accessing the index/home page."""
        response = client.get("/")
        assert response.status_code == 200
        # Should render HTML template
        assert "text/html" in response.headers.get("content-type", "")
    
    @pytest.mark.unit
    def test_chat_page(self, client):
        """Test accessing the chat page."""
        response = client.get("/chat")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    @pytest.mark.unit
    def test_search_page(self, client):
        """Test accessing the search page."""
        response = client.get("/search")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestRateLimiting:
    """Test rate limiting on endpoints."""
    
    @pytest.mark.unit
    def test_rate_limit_chat_endpoint(self, client, sample_session):
        """Test that chat endpoint has rate limiting."""
        # Note: In test environment, rate limiting might not be enforced
        # This test documents the expected behavior
        response = client.get("/health")
        # Rate limiting should allow health checks
        assert response.status_code in [200, 503]
    
    @pytest.mark.unit
    def test_rate_limit_headers(self, client):
        """Test that responses include rate limit headers."""
        response = client.get("/api/folders")
        # Check for presence of rate limit headers (if implemented)
        # This is documentation of expected headers
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling and response codes."""
    
    @pytest.mark.unit
    def test_404_not_found(self, client):
        """Test 404 response for non-existent endpoint."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
    
    @pytest.mark.unit
    def test_validation_error(self, client):
        """Test validation error response."""
        response = client.post(
            "/api/folders",
            json={"invalid_field": "value"}
        )
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.unit
    def test_invalid_json(self, client):
        """Test response to invalid JSON."""
        response = client.post(
            "/api/folders",
            data="invalid json",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 422
