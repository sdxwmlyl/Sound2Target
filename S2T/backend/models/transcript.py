from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from models.database import get_db


@dataclass
class TranscriptSegment:
    id: Optional[int] = None
    audio_file_id: int = 0
    speaker_id: str = "0"
    start_time: float = 0.0
    end_time: float = 0.0
    text: str = ""
    original_text: Optional[str] = None
    edited_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class TranscriptModel:
    @staticmethod
    def create(
        audio_file_id: int,
        speaker_id: str,
        start_time: float,
        end_time: float,
        text: str
    ) -> TranscriptSegment:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO transcript_segments 
                   (audio_file_id, speaker_id, start_time, end_time, text, original_text) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (audio_file_id, speaker_id, start_time, end_time, text, text)
            )
            conn.commit()
            return TranscriptModel.get_by_id(cursor.lastrowid)
    
    @staticmethod
    def create_batch(segments: List[dict]) -> None:
        with get_db() as conn:
            cursor = conn.cursor()
            for seg in segments:
                cursor.execute(
                    """INSERT INTO transcript_segments 
                       (audio_file_id, speaker_id, start_time, end_time, text, original_text) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (seg['audio_file_id'], seg['speaker_id'], seg['start_time'], 
                     seg['end_time'], seg['text'], seg['text'])
                )
            conn.commit()
    
    @staticmethod
    def get_by_id(segment_id: int) -> Optional[TranscriptSegment]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transcript_segments WHERE id = ?", (segment_id,))
            row = cursor.fetchone()
            if row:
                return TranscriptSegment(**dict(row))
            return None
    
    @staticmethod
    def get_by_audio_file(audio_file_id: int) -> List[TranscriptSegment]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM transcript_segments WHERE audio_file_id = ? ORDER BY start_time",
                (audio_file_id,)
            )
            return [TranscriptSegment(**dict(row)) for row in cursor.fetchall()]
    
    @staticmethod
    def update_text(segment_id: int, text: str) -> Optional[TranscriptSegment]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE transcript_segments SET text = ?, edited_at = CURRENT_TIMESTAMP WHERE id = ?",
                (text, segment_id)
            )
            conn.commit()
            return TranscriptModel.get_by_id(segment_id)
    
    @staticmethod
    def delete_by_audio_file(audio_file_id: int) -> int:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM transcript_segments WHERE audio_file_id = ?",
                (audio_file_id,)
            )
            conn.commit()
            return cursor.rowcount
    
    @staticmethod
    def get_text_by_audio_file(audio_file_id: int) -> str:
        segments = TranscriptModel.get_by_audio_file(audio_file_id)
        return "\n".join([f"[{s.start_time:.1f}-{s.end_time:.1f}] {s.speaker_id}: {s.text}" for s in segments])
    
    @staticmethod
    def get_all_text_by_project(project_id: int) -> str:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT ts.speaker_id, ts.start_time, ts.end_time, ts.text, af.audio_name
                   FROM transcript_segments ts
                   JOIN audio_files af ON ts.audio_file_id = af.id
                   WHERE af.project_id = ?
                   ORDER BY af.created_at, ts.start_time""",
                (project_id,)
            )
            rows = cursor.fetchall()
            
            if not rows:
                return ""
            
            lines = []
            current_audio = None
            for row in rows:
                audio_name = row['audio_name']
                if audio_name != current_audio:
                    current_audio = audio_name
                    lines.append(f"\n=== {audio_name} ===")
                
                lines.append(
                    f"[{row['start_time']:.1f}-{row['end_time']:.1f}] "
                    f"发言人{row['speaker_id']}: {row['text']}"
                )
            
            return "\n".join(lines)