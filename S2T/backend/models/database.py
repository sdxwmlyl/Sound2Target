import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator


DB_PATH: Path = None


def init_db(db_path: str = None):
    global DB_PATH
    from config.settings import get_settings
    
    if db_path is None:
        settings = get_settings()
        db_path = settings.database.path
    
    DB_PATH = Path(db_path)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            hotwords TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS audio_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            audio_name TEXT NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            source_type TEXT NOT NULL DEFAULT 'file',
            duration REAL,
            file_size INTEGER,
            status TEXT DEFAULT 'pending',
            summary TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS transcript_segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audio_file_id INTEGER NOT NULL,
            speaker_id TEXT DEFAULT '0',
            start_time REAL NOT NULL,
            end_time REAL NOT NULL,
            text TEXT NOT NULL,
            original_text TEXT,
            edited_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (audio_file_id) REFERENCES audio_files(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS ai_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_audio_project ON audio_files(project_id);
        CREATE INDEX IF NOT EXISTS idx_segments_audio ON transcript_segments(audio_file_id);
        CREATE INDEX IF NOT EXISTS idx_chats_project ON ai_chats(project_id);
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized: {DB_PATH}")


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    global DB_PATH
    if DB_PATH is None:
        init_db()
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_db_path() -> Path:
    global DB_PATH
    if DB_PATH is None:
        init_db()
    return DB_PATH