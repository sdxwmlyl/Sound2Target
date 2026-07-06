from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from models.database import get_db


@dataclass
class Session:
    id: Optional[int] = None
    project_id: int = 0
    name: str = ""
    source_type: str = "file"
    created_at: Optional[datetime] = None


class SessionModel:
    @staticmethod
    def create(project_id: int, name: str, source_type: str = "file") -> Session:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (project_id, name, source_type) VALUES (?, ?, ?)",
                (project_id, name, source_type)
            )
            conn.commit()
            session_id = cursor.lastrowid
            return SessionModel.get_by_id(session_id)
    
    @staticmethod
    def get_by_id(session_id: int) -> Optional[Session]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            if row:
                return Session(**dict(row))
            return None
    
    @staticmethod
    def get_by_project(project_id: int) -> List[Session]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sessions WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,)
            )
            return [Session(**dict(row)) for row in cursor.fetchall()]
    
    @staticmethod
    def update(session_id: int, name: str = None) -> Optional[Session]:
        with get_db() as conn:
            cursor = conn.cursor()
            
            if name is None:
                return SessionModel.get_by_id(session_id)
            
            cursor.execute(
                "UPDATE sessions SET name = ? WHERE id = ?",
                (name, session_id)
            )
            conn.commit()
            return SessionModel.get_by_id(session_id)
    
    @staticmethod
    def delete(session_id: int) -> bool:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0