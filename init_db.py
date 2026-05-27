import sqlite3
import os

db_path = os.path.join('backend', 'services', 'database', 'astronomy_history.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create the metrics table exactly matching your engine parameters
cursor.execute('''
    CREATE TABLE IF NOT EXISTS star_detection_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        image_name TEXT NOT NULL,
        stars_detected INTEGER NOT NULL,
        brightest_star_pixel_value INTEGER NOT NULL,
        average_star_area REAL NOT NULL
    )
''')

conn.commit()
conn.close()
print('✅ Database schema initialized successfully!')
