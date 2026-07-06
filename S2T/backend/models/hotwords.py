from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from models.database import get_db


@dataclass
class Hotword:
    id: Optional[int] = None
    project_id: int = 0
    word: str = ""
    created_at: Optional[datetime] = None


class HotwordModel:
    @staticmethod
    def create(project_id: int, word: str) -> Hotword:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO hotwords (project_id, word) VALUES (?, ?)",
                (project_id, word)
            )
            conn.commit()
            return HotwordModel.get_by_id(cursor.lastrowid)
    
    @staticmethod
    def create_batch(project_id: int, words: List[str]) -> None:
        with get_db() as conn:
            cursor = conn.cursor()
            for word in words:
                word = word.strip()
                if word:
                    cursor.execute(
                        "INSERT OR IGNORE INTO hotwords (project_id, word) VALUES (?, ?)",
                        (project_id, word)
                    )
            conn.commit()
    
    @staticmethod
    def get_by_id(hotword_id: int) -> Optional[Hotword]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM hotwords WHERE id = ?",
                (hotword_id,)
            )
            row = cursor.fetchone()
            if row:
                return Hotword(**dict(row))
            return None
    
    @staticmethod
    def get_by_project(project_id: int) -> List[Hotword]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM hotwords WHERE project_id = ? ORDER BY created_at",
                (project_id,)
            )
            return [Hotword(**dict(row)) for row in cursor.fetchall()]
    
    @staticmethod
    def get_words_by_project(project_id: int) -> List[str]:
        hotwords = HotwordModel.get_by_project(project_id)
        return [hw.word for hw in hotwords]
    
    @staticmethod
    def delete(hotword_id: int) -> bool:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM hotwords WHERE id = ?", (hotword_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete_by_project(project_id: int) -> int:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM hotwords WHERE project_id = ?", (project_id,))
            conn.commit()
            return cursor.rowcount