import os
import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="astronomy_history.db"):
        """
        Manages local SQLite storage for archiving high-confidence 
        satellite passes and transient tracking events.
        """
        # Place database file at the root of the project workspace
        self.db_path = os.path.join(os.getcwd(), db_name)
        self.initialize_database()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def initialize_database(self):
        """Creates the structural tracking tables if they do not exist."""
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
        """
        Inserts a verified high-confidence transient anomaly record into local storage.
        """
        query = '''
            INSERT INTO detection_history 
            (timestamp, classification, confidence_score, line_segments, aspect_ratio, captured_frame_path)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        timestamp_str = datetime.utcnow().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (timestamp_str, classification, confidence, lines, aspect_ratio, frame_path))
            conn.commit()
            inserted_id = cursor.lastrowid
            
        print(f"💾 Event archived successfully in SQLite. Assigned Record ID: [#{inserted_id}]")
        return inserted_id

    def fetch_all_logs(self) -> list:
        """Queries database tracking entries for UI dashboard display ingestion."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM detection_history ORDER BY timestamp DESC")
            rows = cursor.fetchall()
        return rows
