import sys
import numpy as np
import cv2
import os

sys.path.append(os.getcwd())

from backend.services.computer_vision.motion_tracker import TransientMotionDetector
from backend.services.computer_vision.meteor_filter import TransientSignalFilter

def run_elongated_streak_test():
    print("\n--- RUNNING METEOR SATELLITE STREAK VERIFICATION ---")
    
    tracker = TransientMotionDetector(buffer_size=10, min_contour_area=15)
    intelligence_filter = TransientSignalFilter(confidence_threshold=0.65)
    
    for _ in range(10):
        tracker.process_frame(np.zeros((500, 500), dtype=np.uint8))
        
    simulated_sky = np.zeros((500, 500), dtype=np.uint8)
    # Draw a highly elongated, shallow horizontal streak (long width, tiny height footprint)
    cv2.line(simulated_sky, (10, 250), (490, 260), 255, 2)
    
    motion_detected, metadata, processed_mask = tracker.process_frame(simulated_sky)
    
    if motion_detected:
        analysis_result = intelligence_filter.evaluate_motion_profile(processed_mask, metadata)
        
        print("\n[AI Intelligence Filter Analysis Metrics]:")
        print(f"  Detected Movement:    {motion_detected}")
        print(f"  Line Segments Found:  {analysis_result['line_segments_detected']}")
        print(f"  Target Aspect Ratio:  {analysis_result['target_aspect_ratio']}")
        print(f"  Confidence Rating:    {analysis_result['confidence_score'] * 100}%")
        print(f"  Platform Target Typology:  👉 [{analysis_result['classification']}] 👈")
        print(f"  Database Log Approved: {analysis_result['pass_verified']}")
        
        print("\n✅ Sprint 5 Filter validation check complete.")

if __name__ == "__main__":
    run_elongated_streak_test()
