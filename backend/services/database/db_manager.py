import os
import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="astronomy_history.db"):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(current_dir, db_name)
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS target_passes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_name TEXT NOT NULL,
                    scheduled_start DATETIME NOT NULL,
                    scheduled_end DATETIME NOT NULL,
                    max_elevation REAL,
                    status TEXT DEFAULT 'PENDING'
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cv_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pass_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    detection_type TEXT NOT NULL,
                    confidence REAL,
                    image_path TEXT,
                    metrics_json TEXT,
                    FOREIGN KEY (pass_id) REFERENCES target_passes(id) ON DELETE SET NULL
                )
            """)
            conn.commit()
            print(f" Foundation Database initialized successfully at: {self.db_path}")

    def log_pass(self, name, start_time, end_time, max_el):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO target_passes (target_name, scheduled_start, scheduled_end, max_elevation, status)
                VALUES (?, ?, ?, ?, 'TRACKING')
            """, (name, start_time, end_time, max_el))
            conn.commit()
            return cursor.lastrowid

    def log_detection(self, pass_id, det_type, confidence, img_path, metrics="{}"):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cv_detections (pass_id, detection_type, confidence, image_path, metrics_json)
                VALUES (?, ?, ?, ?, ?)
            """, (pass_id, det_type, confidence, img_path, metrics))
            conn.commit()
