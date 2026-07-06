import pytest
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


def test_config_load():
    from config.settings import get_settings
    settings = get_settings()
    assert settings.asr.engine == "funasr"
    assert settings.llm.provider == "ollama"
    assert settings.audio.sample_rate == 16000


def test_database_init():
    from models.database import init_db, get_db
    init_db("./data/test.db")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [t[0] for t in tables]
        
        assert 'projects' in table_names
        assert 'audio_files' in table_names
        assert 'transcript_segments' in table_names
    
    os.remove("./data/test.db")


def test_project_model():
    from models.database import init_db
    from models.project import ProjectModel
    
    init_db("./data/test_project.db")
    
    project = ProjectModel.create("测试项目", "测试描述", "热词1,热词2")
    assert project.id is not None
    assert project.name == "测试项目"
    assert project.hotwords == "热词1,热词2"
    
    fetched = ProjectModel.get_by_id(project.id)
    assert fetched.name == "测试项目"
    
    ProjectModel.update(project.id, hotwords="新热词1,新热词2")
    updated = ProjectModel.get_by_id(project.id)
    assert updated.hotwords == "新热词1,新热词2"
    
    ProjectModel.delete(project.id)
    assert ProjectModel.get_by_id(project.id) is None
    
    os.remove("./data/test_project.db")


def test_audio_file_model():
    from models.database import init_db
    from models.project import ProjectModel
    from models.audio_file import AudioFileModel
    
    init_db("./data/test_audio.db")
    
    project = ProjectModel.create("测试项目")
    
    audio = AudioFileModel.create(
        project_id=project.id,
        audio_name="测试音频",
        filename="test.wav",
        filepath="/tmp/test.wav",
        source_type="file",
        duration=60.0,
        file_size=1024
    )
    
    assert audio.id is not None
    assert audio.status == "pending"
    assert audio.source_type == "file"
    
    updated = AudioFileModel.update_status(audio.id, "completed")
    assert updated.status == "completed"
    
    audios = AudioFileModel.get_by_project(project.id)
    assert len(audios) == 1
    
    os.remove("./data/test_audio.db")


def test_transcript_model():
    from models.database import init_db
    from models.project import ProjectModel
    from models.audio_file import AudioFileModel
    from models.transcript import TranscriptModel
    
    init_db("./data/test_transcript.db")
    
    project = ProjectModel.create("测试项目")
    audio = AudioFileModel.create(project.id, "测试音频", "test.wav", "/tmp/test.wav", "file")
    
    segment = TranscriptModel.create(
        audio_file_id=audio.id,
        speaker_id="0",
        start_time=0.0,
        end_time=5.0,
        text="测试文本"
    )
    
    assert segment.id is not None
    assert segment.text == "测试文本"
    assert segment.original_text == "测试文本"
    
    updated = TranscriptModel.update_text(segment.id, "修改后的文本")
    assert updated.text == "修改后的文本"
    assert updated.edited_at is not None
    
    segments = TranscriptModel.get_by_audio_file(audio.id)
    assert len(segments) == 1
    
    os.remove("./data/test_transcript.db")


def test_project_hotwords():
    from models.database import init_db
    from models.project import ProjectModel
    
    init_db("./data/test_hotwords.db")
    
    project = ProjectModel.create("测试项目", "", "初始热词")
    assert project.hotwords == "初始热词"
    
    ProjectModel.update(project.id, hotwords="新热词1,新热词2,新热词3")
    updated = ProjectModel.get_by_id(project.id)
    assert updated.hotwords == "新热词1,新热词2,新热词3"
    
    os.remove("./data/test_hotwords.db")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])