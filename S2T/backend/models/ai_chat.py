from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from models.database import get_db


@dataclass
class AIChat:
    id: Optional[int] = None
    project_id: int = 0
    role: str = ""
    content: str = ""
    created_at: Optional[datetime] = None


class AIChatModel:
    @staticmethod
    def create(project_id: int, role: str, content: str) -> AIChat:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ai_chats (project_id, role, content) VALUES (?, ?, ?)",
                (project_id, role, content)
            )
            conn.commit()
            return AIChatModel.get_by_id(cursor.lastrowid)
    
    @staticmethod
    def get_by_id(chat_id: int) -> Optional[AIChat]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_chats WHERE id = ?", (chat_id,))
            row = cursor.fetchone()
            if row:
                return AIChat(**dict(row))
            return None
    
    @staticmethod
    def get_by_project(project_id: int, limit: int = 50) -> List[AIChat]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM ai_chats 
                   WHERE project_id = ? 
                   ORDER BY created_at DESC 
                   LIMIT ?""",
                (project_id, limit)
            )
            rows = cursor.fetchall()
            return [AIChat(**dict(row)) for row in reversed(rows)]
    
    @staticmethod
    def delete_by_project(project_id: int) -> int:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ai_chats WHERE project_id = ?", (project_id,))
            conn.commit()
            return cursor.rowcount