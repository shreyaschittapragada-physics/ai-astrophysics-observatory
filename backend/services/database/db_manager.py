import os
import sqlite3
from datetime import datetime, timedelta, timezone

class DatabaseManager:
    def __init__(self, db_name="astronomy_history.db"):
        """
        Manages local SQLite storage for archiving high-confidence 
        satellite passes and transient tracking events.
        """
        self.db_path = os.path.join(os.getcwd(), db_name)
        self.initialize_database()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def initialize_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detection_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    line_segments INTEGER NOT NULL,
                    aspect_ratio REAL NOT NULL,
                    captured_frame_path TEXT
                )
            ''')
            conn.commit()
        print(f"🗄️ SQLite Database Manager initialized at: {self.db_path}")

    def log_detection_event(self, classification: str, confidence: float, lines: int, aspect_ratio: float, frame_path=None) -> int:
        query = '''
            INSERT INTO detection_history 
            (timestamp, classification, confidence_score, line_segments, aspect_ratio, captured_frame_path)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        # Maintain modern timezone-aware parsing conventions
        timestamp_str = datetime.now(timezone.utc).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (timestamp_str, classification, confidence, lines, aspect_ratio, frame_path))
            conn.commit()
            inserted_id = cursor.lastrowid
            
        print(f"💾 Event archived successfully in SQLite. Assigned Record ID: [#{inserted_id}]")
        return inserted_id

    def fetch_all_logs(self) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM detection_history ORDER BY timestamp DESC")
            rows = cursor.fetchall()
        return rows

    def enforce_retention_policy(self, max_hours_noise_retention=24) -> int:
        """
        Scans database logs and purges entries classified as TERRESTRIAL_NOISE
        if they exceed the retention window, preventing storage bloat on edge units.
        
        :returns: Number of deleted records.
        """
        print("🧹 Running automated storage log retention maintenance sweep...")
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_hours_noise_retention)
        cutoff_str = cutoff_time.isoformat()
        
        query = '''
            DELETE FROM detection_history
            WHERE classification = 'TERRESTRIAL_NOISE' AND timestamp < ?
        '''
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (cutoff_str,))
            conn.commit()
            purged_count = cursor.rowcount
            
        if purged_count > 0:
            print(f"♻️ Edge Storage Guard: Purged {purged_count} stale terrestrial noise records from local database.")
        else:
            print("🛡️ Edge Storage Guard: No stale terrestrial noise logs found. Storage profile nominal.")
        return purged_count
