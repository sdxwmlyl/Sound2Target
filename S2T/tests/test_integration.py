import pytest
import sys
import os
import asyncio
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi.testclient import TestClient
from main import app
from models.database import init_db
from models.project import ProjectModel
from models.session import SessionModel
from models.audio_file import AudioFileModel


@pytest.fixture(scope="module")
def test_db():
    init_db("./data/test_integration.db")
    yield
    os.remove("./data/test_integration.db")


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_full_workflow(test_db, client):
    resp = client.post("/api/projects", json={"name": "集成测试项目", "description": "测试描述"})
    assert resp.status_code == 200
    project_id = resp.json()["id"]
    
    resp = client.get(f"/api/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "集成测试项目"
    
    resp = client.post(f"/api/projects/{project_id}/sessions", json={"name": "测试会话", "source_type": "file"})
    assert resp.status_code == 200
    session_id = resp.json()["id"]
    
    test_audio = os.path.join(os.path.dirname(__file__), "..", "ProjectSound2Answer", "backend", "test_cable.wav")
    if not os.path.exists(test_audio):
        test_audio = tempfile.mktemp(suffix=".wav")
        import soundfile as sf
        import numpy as np
        sf.write(test_audio, np.zeros(16000, dtype=np.int16), 16000)
    
    with open(test_audio, "rb") as f:
        resp = client.post(f"/api/sessions/{session_id}/upload", files={"file": ("test.wav", f, "audio/wav")})
    
    assert resp.status_code == 200
    audio_file_id = resp.json()["id"]
    
    resp = client.get(f"/api/audio-files/{audio_file_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"
    
    resp = client.post(f"/api/projects/{project_id}/hotwords", json={"words": ["人工智能", "测试"]})
    assert resp.status_code == 200
    
    resp = client.get("/api/projects")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    
    resp = client.delete(f"/api/projects/{project_id}")
    assert resp.status_code == 200


def test_config_endpoint(client):
    resp = client.get("/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "llm_provider" in data
    assert "asr_engine" in data
    assert "supported_formats" in data


def test_audio_devices_endpoint(client):
    resp = client.get("/api/audio/devices")
    assert resp.status_code == 200
    data = resp.json()
    assert "devices" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])