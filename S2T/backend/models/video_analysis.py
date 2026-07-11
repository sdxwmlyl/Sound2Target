from datetime import datetime
from typing import Optional, List, Dict
from models.database import get_db


class VideoAnalysisModel:
    @staticmethod
    def create_table():
        """创建视频分析任务表（如不存在）"""
        with get_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS video_analysis_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    url TEXT NOT NULL,
                    video_title TEXT,
                    video_duration REAL,
                    summary_prompt TEXT,
                    sample_interval INTEGER DEFAULT 30,
                    status TEXT DEFAULT 'pending',
                    audio_file_id INTEGER,
                    transcript_segments INTEGER DEFAULT 0,
                    frames_captured INTEGER DEFAULT 0,
                    frames_analyzed INTEGER DEFAULT 0,
                    content_items INTEGER DEFAULT 0,
                    summary TEXT,
                    merged_content TEXT,
                    error_message TEXT,
                    created_at TEXT DEFAULT (datetime('now','localtime')),
                    updated_at TEXT DEFAULT (datetime('now','localtime'))
                )
            """)
            conn.commit()

    @staticmethod
    def create(url: str, project_id: int = None, summary_prompt: str = "",
               sample_interval: int = 30) -> Dict:
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO video_analysis_tasks (url, project_id, summary_prompt, sample_interval) "
                "VALUES (?, ?, ?, ?)",
                (url, project_id, summary_prompt, sample_interval)
            )
            conn.commit()
            return VideoAnalysisModel.get_by_id(cursor.lastrowid)

    @staticmethod
    def get_by_id(task_id: int) -> Optional[Dict]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM video_analysis_tasks WHERE id=?", (task_id,)
            ).fetchone()
            if row:
                return dict(row)
            return None

    @staticmethod
    def update(task_id: int, **kwargs):
        with get_db() as conn:
            kwargs['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sets = ", ".join(f"{k}=?" for k in kwargs)
            vals = list(kwargs.values()) + [task_id]
            conn.execute(
                f"UPDATE video_analysis_tasks SET {sets} WHERE id=?", vals
            )
            conn.commit()

    @staticmethod
    def get_all(limit: int = 50) -> List[Dict]:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM video_analysis_tasks ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
