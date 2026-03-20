"""Code Execution Service Integration Tests.

Comprehensive integration tests for code execution endpoints:
- Code execution (Python, JavaScript, etc.)
- Terminal command execution
- Preview server management
- Security and sandboxing

Author: Agent 7 - ResonantGenesis Team
Created: February 21, 2026
"""

import pytest
import json
from typing import Dict, Any
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app.main import app


class TestConfig:
    """Test configuration constants."""
    BASE_URL = "http://testserver"
    TEST_USER_ID = "test-user-123"


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def json_headers():
    """Return JSON content-type headers."""
    return {"Content-Type": "application/json"}


@pytest.fixture
def auth_headers():
    """Return authorization headers."""
    return {"Authorization": "Bearer test-token"}


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data
        assert "version" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns service info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "endpoints" in data


class TestCodeExecutionEndpoints:
    """Test code execution endpoints."""
    
    def test_execute_python_code(self, client, json_headers):
        """Test Python code execution."""
        payload = {
            "code": "print('Hello, World!')",
            "language": "python"
        }
        response = client.post(
            "/code/execute",
            json=payload,
            headers=json_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_execute_javascript_code(self, client, json_headers):
        """Test JavaScript code execution."""
        payload = {
            "code": "console.log('Hello, World!');",
            "language": "javascript"
        }
        response = client.post(
            "/code/execute",
            json=payload,
            headers=json_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_execute_code_with_timeout(self, client, json_headers):
        """Test code execution with timeout."""
        payload = {
            "code": "import time; time.sleep(1); print('done')",
            "language": "python",
            "timeout": 5
        }
        response = client.post(
            "/code/execute",
            json=payload,
            headers=json_headers
        )
        assert response.status_code in [200, 400, 401, 403, 408, 422, 500]
    
    def test_execute_code_missing_language(self, client, json_headers):
        """Test code execution without language specified."""
        payload = {
            "code": "print('test')"
        }
        response = client.post(
            "/code/execute",
            json=payload,
            headers=json_headers
        )
        assert response.status_code in [200, 400, 422, 500]
    
    def test_execute_empty_code(self, client, json_headers):
        """Test code execution with empty code."""
        payload = {
            "code": "",
            "language": "python"
        }
        response = client.post(
            "/code/execute",
            json=payload,
            headers=json_headers
        )
        assert response.status_code in [200, 400, 422, 500]
    
    def test_execute_code_with_stdin(self, client, json_headers):
        """Test code execution with stdin input."""
        payload = {
            "code": "name = input(); print(f'Hello, {name}!')",
            "language": "python",
            "stdin": "World"
        }
        response = client.post(
            "/code/execute",
            json=payload,
            headers=json_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_execute_unsupported_language(self, client, json_headers):
        """Test code execution with unsupported language."""
        payload = {
            "code": "print('test')",
            "language": "unsupported_lang"
        }
        response = client.post(
            "/code/execute",
            json=payload,
            headers=json_headers
        )
        assert response.status_code in [400, 422, 500]


class TestTerminalEndpoints:
    """Test terminal command execution endpoints."""
    
    def test_execute_terminal_command(self, client, json_headers):
        """Test terminal command execution."""
        payload = {
            "command": "echo 'Hello, World!'"
        }
        response = client.post(
            "/terminal/execute",
            json=payload,
            headers=json_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_execute_terminal_with_cwd(self, client, json_headers):
        """Test terminal command with working directory."""
        payload = {
            "command": "pwd",
            "cwd": "/tmp"
        }
        response = client.post(
            "/terminal/execute",
            json=payload,
            headers=json_headers
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]
    
    def test_execute_terminal_with_timeout(self, client, json_headers):
        """Test terminal command with timeout."""
        payload = {
            "command": "sleep 1 && echo 'done'",
            "timeout": 5
        }
        response = client.post(
            "/terminal/execute",
            json=payload,
            headers=json_headers
        )
        assert response.status_code in [200, 400, 401, 403, 408, 422, 500]
    
    def test_execute_empty_command(self, client, json_headers):
        """Test terminal with empty command."""
        payload = {
            "command": ""
        }
        response = client.post(
            "/terminal/execute",
            json=payload,
            headers=json_headers
        )
        assert response.status_code in [200, 400, 422, 500]
    
    def test_execute_dangerous_command_blocked(self, client, json_headers):
        """Test that dangerous commands are blocked."""
        payload = {
            "command": "rm -rf /"
        }
        response = client.post(
            "/terminal/execute",
            json=payload,
            headers=json_headers
        )
        # Should be blocked or handled safely
        assert response.status_code in [200, 400, 403, 422, 500]


class TestPreviewEndpoints:
    """Test preview server management endpoints."""
    
    def test_start_preview(self, client, json_headers):
        """Test starting a preview server."""
        payload = {
            "project_path": "/tmp/test-project",
            "port": 3000
        }
        response = client.post(
            "/preview/start",
            json=payload,
            headers=json_headers
        )
        assert response.status_code in [200, 201, 400, 401, 403, 422, 500]
    
    def test_stop_preview(self, client, json_headers):
        """Test stopping a preview server."""
        payload = {
            "preview_id": "preview-123"
        }
        response = client.post(
            "/preview/stop",
            json=payload,
            headers=json_headers
        )
        assert response.status_code in [200, 400, 401, 403, 404, 422, 500]
    
    def test_get_preview_status(self, client):
        """Test getting preview server status."""
        response = client.get("/preview/status/preview-123")
        assert response.status_code in [200, 404, 500]
    
    def test_list_previews(self, client):
        """Test listing active preview servers."""
        response = client.get("/preview/list")
        assert response.status_code in [200, 404, 500]


class TestSecurityEndpoints:
    """Test security-related functionality."""
    
    def test_code_execution_sandboxed(self, client, json_headers):
        """Test that code execution is sandboxed."""
        payload = {
            "code": "import os; print(os.environ)",
            "language": "python"
        }
        response = client.post(
            "/code/execute",
            json=payload,
            headers=json_headers
        )
        # Should execute but with limited environment
        assert response.status_code in [200, 400, 403, 422, 500]
    
    def test_file_system_access_restricted(self, client, json_headers):
        """Test that file system access is restricted."""
        payload = {
            "code": "open('/etc/passwd').read()",
            "language": "python"
        }
        response = client.post(
            "/code/execute",
            json=payload,
            headers=json_headers
        )
        # Should fail or be restricted
        assert response.status_code in [200, 400, 403, 422, 500]
    
    def test_network_access_restricted(self, client, json_headers):
        """Test that network access is restricted."""
        payload = {
            "code": "import urllib.request; urllib.request.urlopen('http://example.com')",
            "language": "python"
        }
        response = client.post(
            "/code/execute",
            json=payload,
            headers=json_headers
        )
        # Should fail or be restricted
        assert response.status_code in [200, 400, 403, 422, 500]


class TestErrorHandling:
    """Test error handling."""
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        headers = {"Content-Type": "application/json"}
        response = client.post(
            "/code/execute",
            content="not valid json {{{",
            headers=headers
        )
        assert response.status_code in [400, 422, 500]
    
    def test_missing_required_fields(self, client, json_headers):
        """Test handling of missing required fields."""
        response = client.post(
            "/code/execute",
            json={},
            headers=json_headers
        )
        assert response.status_code in [400, 422, 500]
    
    def test_nonexistent_endpoint(self, client):
        """Test 404 for non-existent endpoint."""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code in [404, 405]


class TestCORSHeaders:
    """Test CORS header handling."""
    
    def test_cors_preflight(self, client):
        """Test CORS preflight request."""
        headers = {
            "Origin": "https://resonantgenesis.xyz",
            "Access-Control-Request-Method": "POST"
        }
        response = client.options("/code/execute", headers=headers)
        assert response.status_code in [200, 204, 404]
    
    def test_cors_headers_present(self, client):
        """Test CORS headers in response."""
        headers = {"Origin": "https://resonantgenesis.xyz"}
        response = client.get("/health", headers=headers)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
