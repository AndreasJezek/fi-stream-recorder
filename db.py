import sqlite3
from typing import List, Dict, Optional
from contextlib import contextmanager
import os
from loguru import logger


DB_LOCATION = os.path.join(os.path.dirname(__file__), "db", "fi-recordings.db")


class RecordingDB:
    def __init__(self, db_path: str = DB_LOCATION):
        os.makedirs(os.path.dirname(DB_LOCATION), exist_ok=True)
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        """Context manager for safe database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            self._create_tables(cursor)
            yield cursor
            conn.commit()
        except Exception as e:
            logger.error(f'{str(e)}')
            conn.rollback()
            raise
        finally:
            conn.close()

    def _create_tables(self, cursor: sqlite3.Cursor):
        """Create tables if they don't exist."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recordings(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                cloud_url TEXT,
                expire_epoch INTEGER,
                recording_status TEXT NOT NULL,
                CHECK (recording_status IN ('pending', 'active', 'expired', 'error'))
            )
        """)


    def insert_recording(
        self, name: str, recording_status: str, cloud_url: str = ""
    ) -> int | None:
        """Insert a new recording and return its ID."""
        with self.get_connection() as cursor:
            cursor.execute(
                "INSERT INTO recordings (name, cloud_url, recording_status) VALUES (?, ?, ?)",
                (name, cloud_url, recording_status),
            )
            return cursor.lastrowid

    def update_recording_status(self, name: str, new_status: str) -> int | None:
        with self.get_connection() as cursor:
            cursor.execute(
                ("UPDATE recordings SET recording_status = ?" "WHERE name = ?"),
                (new_status, name),
            )
            return cursor.lastrowid

    def set_recording_url(self, name: str, cloud_url: str, expire_epoch: int) -> int | None:
        with self.get_connection() as cursor:
            cursor.execute(
                "UPDATE recordings SET recording_status = 'active', cloud_url = ?, expire_epoch = ? WHERE name = ?",
                (cloud_url, expire_epoch, name),
            )
            return cursor.rowcount 


    def get_recordings(self, status: Optional[list[str]] = None) -> List[Dict]:
        """Get all recordings, optionally filtered by status."""
        with self.get_connection() as cursor:
            if status and len(status):
                cursor.execute(
                    "SELECT * FROM recordings WHERE recording_status in ?", (status,)
                )
            else:
                cursor.execute("SELECT * FROM recordings")
            return [dict(row) for row in cursor.fetchall()]
