import os
import sys
import cv2
import time
import numpy as np
import sqlite3

# Append project workspace root to sys.path
sys.path.append(os.getcwd())

from backend.services.cv_factory import CVObservationFactory

def initialize_performance_table():
    """Ensures a relational table exists in SQLite to store factory stress metrics."""
    db_path = os.path.join("backend", "services", "database", "astronomy_history.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS factory_performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                iterations INTEGER,
                mean_latency_ms REAL,
                jitter_ms REAL,
                max_latency_ms REAL,
                theoretical_fps REAL,
                verdict TEXT
            )
        """)
        conn.commit()

def log_factory_metrics(iterations, mean_lat, jitter, max_lat, fps, verdict):
    """Commits the performance telemetry indicators to your SQLite database."""
    db_path = os.path.join("backend", "services", "database", "astronomy_history.db")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO factory_performance_metrics 
            (timestamp, iterations, mean_latency_ms, jitter_ms, max_latency_ms, theoretical_fps, verdict)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, iterations, mean_lat, jitter, max_lat, fps, verdict))
        conn.commit()

def run_performance_benchmark():
    print("\n--- BEGINNING CV CORE PIPELINE HIGH-THROUGHPUT PERFORMANCE STRESS TEST ---")
    
    # Ensure the DB table exists before starting
    initialize_performance_table()
    
    factory = CVObservationFactory()
    
    # Generate a realistic 1080p high-resolution frame to simulate an HD telescope stream feed
    print("🖥️ Generating 1920x1080 synthetic star-field frame matrix...")
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    for _ in range(200):
        y, x = np.random.randint(0, 1080), np.random.randint(0, 1920)
        cv2.circle(frame, (x, y), np.random.randint(1, 3), (255, 255, 255), -1)

    iterations = 100
    latencies = []
    
    print(f"⚡ Simulating streaming workload loop over {iterations} continuous frame arrays...")
    
    for i in range(iterations):
        start_time = time.perf_counter()
        
        # Execute the unified processing sequence under load
        _ = factory.analyze_frame_brightness(frame)
        _, _ = factory.isolate_star_fields(frame)
        
        duration = time.perf_counter() - start_time
        latencies.append(duration)
        
        if (i + 1) % 25 == 0:
            print(f"   Processed {i + 1}/{iterations} iterations...")

    # Calculate precise telemetry analytics
    latencies = np.array(latencies) * 1000  # Convert to milliseconds
    mean_latency = np.mean(latencies)
    max_latency = np.max(latencies)
    min_latency = np.min(latencies)
    std_dev = np.std(latencies)
    achievable_fps = 1000.0 / mean_latency

    print("\n📊 COMPUTER VISION CORE PERFORMANCE REPORT:")
    print("--------------------------------------------------")
    print(f" ⏱️ Mean Processing Latency:  {mean_latency:.3f} ms / frame")
    print(f" 🎚️ Jitter (Std Dev):         {std_dev:.3f} ms")
    print(f" 🔺 Max Peak Latency:         {max_latency:.3f} ms")
    print(f" 🔻 Min Latency:              {min_latency:.3f} ms")
    print(f" 🚀 Theoretical Processing Ceiling: {achievable_fps:.2f} FPS")
    print("--------------------------------------------------")
    
    if achievable_fps >= 30.0:
        verdict = "PASSED"
        print("✅ STABILITY VERDICT: PASSED. Overhead is low enough for a 30 FPS hardware camera feed.")
    else:
        verdict = "WARNING"
        print("⚠️ STABILITY VERDICT: WARNING. Performance might drop frames on high-resolution continuous streams.")

    # Save metrics to the database
    log_factory_metrics(iterations, mean_latency, std_dev, max_latency, achievable_fps, verdict)
    print("💾 Performance profile saved successfully to SQLite [factory_performance_metrics].")

if __name__ == "__main__":
    run_performance_benchmark()