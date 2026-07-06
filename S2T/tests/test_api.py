import pytest
import sys
import os
import asyncio
import tempfile
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

BASE_URL = "http://localhost:8000"


def test_api_workflow():
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except:
        pytest.skip("Server not running")
    
    resp = requests.post(f"{BASE_URL}/api/projects", json={"name": "API测试项目", "description": "测试"})
    assert resp.status_code == 200
    project_id = resp.json()["id"]
    
    resp = requests.get(f"{BASE_URL}/api/projects/{project_id}")
    assert resp.status_code == 200
    
    resp = requests.post(f"{BASE_URL}/api/projects/{project_id}/sessions", json={"name": "测试会话", "source_type": "file"})
    assert resp.status_code == 200
    session_id = resp.json()["id"]
    
    resp = requests.post(f"{BASE_URL}/api/projects/{project_id}/hotwords", json={"words": ["测试词"]})
    assert resp.status_code == 200
    
    resp = requests.get(f"{BASE_URL}/config")
    assert resp.status_code == 200
    
    resp = requests.delete(f"{BASE_URL}/api/projects/{project_id}")
    assert resp.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])