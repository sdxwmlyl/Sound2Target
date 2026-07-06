from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from models.database import get_db


@dataclass
class AudioFile:
    id: Optional[int] = None
    project_id: int = 0
    audio_name: str = ""
    filename: str = ""
    filepath: str = ""
    source_type: str = "file"
    duration: Optional[float] = None
    file_size: Optional[int] = None
    status: str = "pending"
    summary: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


class AudioFileModel:
    @staticmethod
    def create(
        project_id: int,
        audio_name: str,
        filename: str,
        filepath: str,
        source_type: str = "file",
        duration: float = None,
        file_size: int = None
    ) -> AudioFile:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO audio_files 
                   (project_id, audio_name, filename, filepath, source_type, duration, file_size) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (project_id, audio_name, filename, filepath, source_type, duration, file_size)
            )
            conn.commit()
            return AudioFileModel.get_by_id(cursor.lastrowid)
    
    @staticmethod
    def get_by_id(audio_id: int) -> Optional[AudioFile]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audio_files WHERE id = ?", (audio_id,))
            row = cursor.fetchone()
            if row:
                return AudioFile(**dict(row))
            return None
    
    @staticmethod
    def get_by_project(project_id: int) -> List[AudioFile]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM audio_files WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,)
            )
            return [AudioFile(**dict(row)) for row in cursor.fetchall()]
    
    @staticmethod
    def update_status(audio_id: int, status: str, error_message: str = None) -> Optional[AudioFile]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE audio_files SET status = ?, error_message = ? WHERE id = ?",
                (status, error_message, audio_id)
            )
            conn.commit()
            return AudioFileModel.get_by_id(audio_id)
    
    @staticmethod
    def update_audio_name(audio_id: int, audio_name: str) -> Optional[AudioFile]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE audio_files SET audio_name = ? WHERE id = ?",
                (audio_name, audio_id)
            )
            conn.commit()
            return AudioFileModel.get_by_id(audio_id)
    
    @staticmethod
    def delete(audio_id: int) -> bool:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM audio_files WHERE id = ?", (audio_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def update_duration(audio_id: int, duration: float) -> Optional[AudioFile]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE audio_files SET duration = ? WHERE id = ?",
                (duration, audio_id)
            )
            conn.commit()
            return AudioFileModel.get_by_id(audio_id)
    
    @staticmethod
    def update_summary(audio_id: int, summary: str) -> Optional[AudioFile]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE audio_files SET summary = ? WHERE id = ?",
                (summary, audio_id)
            )
            conn.commit()
            return AudioFileModel.get_by_id(audio_id)
    
    @staticmethod
    def get_active_recording(project_id: int) -> Optional[AudioFile]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM audio_files 
                   WHERE project_id = ? AND source_type IN ('microphone', 'system') AND status = 'processing'
                   LIMIT 1""",
                (project_id,)
            )
            row = cursor.fetchone()
            if row:
                return AudioFile(**dict(row))
            return None