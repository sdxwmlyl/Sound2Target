from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from models.database import get_db


@dataclass
class Project:
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    hotwords: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProjectModel:
    @staticmethod
    def create(name: str, description: str = "", hotwords: str = "") -> Project:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO projects (name, description, hotwords) VALUES (?, ?, ?)",
                (name, description, hotwords)
            )
            conn.commit()
            return ProjectModel.get_by_id(cursor.lastrowid)
    
    @staticmethod
    def get_by_id(project_id: int) -> Optional[Project]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            if row:
                return Project(**dict(row))
            return None
    
    @staticmethod
    def get_all() -> List[Project]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
            return [Project(**dict(row)) for row in cursor.fetchall()]
    
    @staticmethod
    def update(project_id: int, name: str = None, description: str = None, hotwords: str = None) -> Optional[Project]:
        with get_db() as conn:
            cursor = conn.cursor()
            
            updates = []
            values = []
            if name is not None:
                updates.append("name = ?")
                values.append(name)
            if description is not None:
                updates.append("description = ?")
                values.append(description)
            if hotwords is not None:
                updates.append("hotwords = ?")
                values.append(hotwords)
            
            if not updates:
                return ProjectModel.get_by_id(project_id)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(project_id)
            
            cursor.execute(
                f"UPDATE projects SET {', '.join(updates)} WHERE id = ?",
                values
            )
            conn.commit()
            return ProjectModel.get_by_id(project_id)
    
    @staticmethod
    def delete(project_id: int) -> bool:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            return cursor.rowcount > 0