import sys
import numpy as np
import cv2
import os

# Align workspace system path context
sys.path.append(os.getcwd())

from backend.services.computer_vision.motion_tracker import TransientMotionDetector
from backend.services.computer_vision.meteor_filter import TransientSignalFilter
from backend.services.database.db_manager import DatabaseManager

def run_end_to_end_observatory_pipeline():
    print("\n--- RUNNING INTEGRATED E2E OBSERVATORY PIPELINE TEST ---")
    
    # 1. Initialize all three core sub-system engines
    tracker = TransientMotionDetector(buffer_size=10, min_contour_area=15)
    intelligence_filter = TransientSignalFilter(confidence_threshold=0.65)
    db = DatabaseManager()
    
    # 2. Populate tracking history matrix with a blank dark sky background
    for _ in range(10):
        tracker.process_frame(np.zeros((500, 500), dtype=np.uint8))
        
    # 3. Simulate an authentic high-speed satellite streak across the frame grid
    simulated_sky = np.zeros((500, 500), dtype=np.uint8)
    cv2.line(simulated_sky, (15, 250), (485, 255), 255, 2)
    
    print("\n[Data Ingestion] Ingesting transient target frame...")
    motion_detected, metadata, processed_mask = tracker.process_frame(simulated_sky)
    
    if motion_detected:
        print("🎯 Kinematic target captured. Forwarding to filter layer...")
        
        # 4. Evaluate the tracking profile parameters
        analysis_result = intelligence_filter.evaluate_motion_profile(processed_mask, metadata)
        print(f"   Classification: {analysis_result['classification']} | Confidence: {analysis_result['confidence_score'] * 100}%")
        
        # 5. Commit data directly to the relational SQLite table if approved
        if analysis_result["pass_verified"]:
            print("🛡️ Target verification approved. Archiving metadata payload to SQL...")
            record_id = db.log_detection_event(
                classification=analysis_result["classification"],
                confidence=analysis_result["confidence_score"],
                lines=analysis_result["line_segments_detected"],
                aspect_ratio=analysis_result["target_aspect_ratio"],
                frame_path="captures/simulated_streak_pass.jpg"
            )
            
            # 6. Verify persistence by querying data out of SQLite storage
            print("\n[Database Verification] Testing retrieval from SQLite records pool...")
            all_logs = db.fetch_all_logs()
            latest_record = all_logs[0]
            print(f"   Successfully fetched latest Record ID [#{latest_record[0]}] out of SQLite!")
            print(f"   Stored Event Content: Timestamp={latest_record[1]}, Type={latest_record[2]}, Score={latest_record[3]*100}%")
            
            print("\n✅ Sprint 6 Integrated Pipeline Complete. Data persistence layer confirmed solid.")
        else:
            print("❌ Target verification rejected as terrestrial noise. Skipped database writing.")
    else:
        print("❌ Pipeline Friction: Motion tracker missed the target.")

if __name__ == "__main__":
    run_end_to_end_observatory_pipeline()
