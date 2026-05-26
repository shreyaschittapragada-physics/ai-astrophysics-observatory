import cv2
import numpy as np
import time
import os
import sys
from backend.services.tracking.iss_tracker import ISSTracker
from backend.services.tracking.horizon_mask import HorizonMaskEngine
from backend.services.computer_vision.motion_tracker import TransientMotionDetector
from backend.services.computer_vision.meteor_filter import TransientSignalFilter
from backend.services.database.db_manager import DatabaseManager

# CRITICAL CODES FILTER: V2 will ONLY activate if one of these exact targets passes your horizon
MAJOR_COORDINATES_WATCHLIST = [
    "ISS (ZARYA)",
    "TIANGONG",
    "HUBBLE"
]

def run_independent_mode(video_source, tracker, intelligence_filter, db):
    """MODE 1: Independent Analysis. Processes a video asset directly without tracking locks."""
    print(f"\n🎬 [INDEPENDENT MODE ACTIVE]")
    print(f"📡 Processing standalone video channel asset: {video_source}")
    
    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"❌ Error: Could not open video source: {video_source}")
        return

    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            
            resized = cv2.resize(frame, (960, 540))
            motion_detected, metadata, mask = tracker.process_stream_frame(resized)
            
            if motion_detected and frame_count % 10 == 0:
                analysis = intelligence_filter.evaluate_motion_profile(mask, metadata)
                print(f"   ⚡ [Frame {frame_count:04d}] Motion detected in independent pass.")
                
                db.log_detection_event(
                    classification="INDEPENDENT_ANOMALY",
                    confidence=analysis["confidence_score"],
                    lines=analysis["line_segments_detected"],
                    aspect_ratio=analysis["target_aspect_ratio"],
                    frame_path="datasets/sky_images/sky.jpg"
                )
    finally:
        cap.release()
        print("✅ Independent video file processing complete.")

def run_targeted_dependent_mode(tracker_v1, horizon_mask, cv_detector_v2, intelligence_filter, db):
    """MODE 2: Targeted Dependent Interlock. 
    Only pairs V1 + V2 if a MAJOR coordinate on our watchlist clears the horizon mask.
    """
    print("\n🛰️ [TARGETED DEPENDENT INTERLOCK MODE ACTIVE]")
    print(f"👁️ Watchlist Active: {MAJOR_COORDINATES_WATCHLIST}")
    
    positions = tracker_v1.calculate_positions()
    active_target = None
    
    for name, telemetry in positions.items():
        az = telemetry["azimuth"]
        el = telemetry["elevation"]
        
        # 1. First Gate: Is it a major coordinate we actually care about?
        if name not in MAJOR_COORDINATES_WATCHLIST:
            print(f"   ⏭️ SKIPPED: {name} (Not on Major Coordinates watch list)")
            continue
            
        # 2. Second Gate: Is the major target clearing our local horizon mask?
        is_blocked = horizon_mask.is_target_obstructed(azimuth=az, elevation=el)
        
        if not is_blocked:
            print(f"   🟢 MAJOR TARGET DETECTED OVERHEAD: {name} (Az: {az}°, El: {el}°)")
            active_target = name
            break
        else:
            print(f"   ❌ OBSTRUCTED MAJOR TARGET: {name} is hidden behind mask (Az: {az}°, El: {el}°)")

    # 3. Activation Gate
    if active_target:
        print(f"\n🎯 INTERLOCK ENGAGED: Activating V2 CV Engine for [{active_target}] pass...")
        image_path = os.path.join("datasets", "sky_images", "sky.jpg")
        if os.path.exists(image_path):
            frame = cv2.imread(image_path)
            _, metadata, mask = cv_detector_v2.process_stream_frame(frame)
            analysis = intelligence_filter.evaluate_motion_profile(mask, metadata)
            
            db.log_detection_event(
                classification=f"DEPENDENT_{active_target.replace(' ', '_')}",
                confidence=0.98,
                lines=analysis["line_segments_detected"],
                aspect_ratio=analysis["target_aspect_ratio"],
                frame_path=image_path
            )
    else:
        print("\n💤 System Idle: No major coordinates currently match active visibility windows.")

def main():
    print("🚀 Project AstroEdge: Universal Hybrid Core Engine Initialized.")
    
    tracker_v1 = ISSTracker()
    horizon_mask = HorizonMaskEngine()
    cv_detector_v2 = TransientMotionDetector(buffer_size=15, min_contour_area=30)
    intelligence_filter = TransientSignalFilter(confidence_threshold=0.60)
    db = DatabaseManager()

    if len(sys.argv) > 1:
        # If an argument is provided, bypass V1 entirely and treat V2 as independent
        video_source = sys.argv[1]
        run_independent_mode(video_source, cv_detector_v2, intelligence_filter, db)
    else:
        # Default behavior: run targeted tracking interlock pass
        run_targeted_dependent_mode(tracker_v1, horizon_mask, cv_detector_v2, intelligence_filter, db)

if __name__ == '__main__':
    main()