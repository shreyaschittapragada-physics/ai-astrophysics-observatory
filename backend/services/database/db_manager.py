import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="astronomy_history.db"):
        self.db_path = os.path.join(os.getcwd(), "backend", "services", "database", db_name)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.initialize_schema()

    def initialize_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detection_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    line_segments_detected INTEGER,
                    target_aspect_ratio REAL,
                    frame_path TEXT
                )
            """)
            conn.commit()

    def log_detection_event(self, classification, confidence, lines, aspect_ratio, frame_path):
        """Inserts a verified CV telemetry event entry directly into SQLite storage."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO detection_events 
                (timestamp, classification, confidence, line_segments_detected, target_aspect_ratio, frame_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, classification, confidence, lines, aspect_ratio, frame_path))
            conn.commit()
        print(f"💾 Database Layer: Saved verified entry as [{classification}] with {confidence*100:.1f}% confidence.")

    def fetch_all_logs(self):
        """
        ADDITION: Fetches all tracked execution logs from database storage.
        Resolves endpoint dependency execution errors in tracking/router.py.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, classification, confidence, 
                       line_segments_detected, target_aspect_ratio, frame_path 
                FROM detection_events 
                ORDER BY timestamp DESC
            """)
            return cursor.fetchall()