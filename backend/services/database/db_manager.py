import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="astronomy_history.db"):
        db_dir = os.path.join("backend", "services", "database")
        os.makedirs(db_dir, exist_ok=True)
        self.db_path = os.path.join(db_dir, db_name)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT DEFAULT 'motion_detected',
                confidence_score REAL DEFAULT 0.0,
                saved_path TEXT,
                v1_sat_name TEXT DEFAULT 'N/A',
                v1_is_above_horizon BOOLEAN DEFAULT 0,
                v2_largest_contour INTEGER
            )
        ''')
        self.conn.commit()

    def log_event(self, v2_report, v1_context=None):
        cursor = self.conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        saved_path = v2_report.get("metadata", {}).get("saved_path", "")
        largest_contour = v2_report.get("metadata", {}).get("largest_contour_area", 0)
        sat_name = v1_context.get("name", "N/A") if v1_context else "N/A"
        is_above_horizon = bool(v1_context.get("is_above_horizon", False)) if v1_context else False
        cursor.execute('''
            INSERT INTO detections (timestamp, saved_path, v1_sat_name, v1_is_above_horizon, v2_largest_contour)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, saved_path, sat_name, is_above_horizon, largest_contour))
        self.conn.commit()
        return cursor.lastrowid
