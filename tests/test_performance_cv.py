import sys
import numpy as np
import cv2

# Bind workspace path context
sys.path.append(sys.path[0] + "/..")
from backend.services.computer_vision.motion_tracker import TransientMotionDetector

def run_motion_simulation():
    print("\n--- INITIATING SPRINT 4 MOTION TRACKER & RING BUFFER TEST ---")
    
    # Instantiate tracker with 15 frames of context storage capacity
    detector = TransientMotionDetector(buffer_size=15, min_contour_area=20)
    
    # 1. Generate 20 frames of perfectly dark, quiet baseline night sky (fills buffer)
    print("🌌 Simulating quiet static night sky (populating ring buffer)...")
    for _ in range(20):
        static_frame = np.zeros((720, 1280), dtype=np.uint8)
        detector.process_frame(static_frame)

    # 2. Introduce an artificial high-speed satellite streak into frame 21
    print("💫 Introducing moving transient streak target matrix...")
    active_frame = np.zeros((720, 1280), dtype=np.uint8)
    # Draw a simulated linear trail line segment representation
    cv2.line(active_frame, (100, 100), (140, 130), 255, 3)
    
    motion_flag, telemetry, _ = detector.process_frame(active_frame)
    
    print("\n[Execution Output Metrics]:")
    print(f"  Motion Detected Triggered: {motion_flag}")
    print(f"  Cached Pre-Motion Ring Buffer Size: {telemetry['buffered_context_frames']} frames")
    print(f"  Tracked Active Target Count: {telemetry['active_target_count']}")
    
    if motion_flag and telemetry['kinematic_vectors']:
        vector = telemetry['kinematic_vectors'][0]
        print(f"  Extracted Centroid Coordinate: {vector['centroid']}")
        print(f"  Pixel Cluster Footprint Area: {vector['pixel_area']} px")
        print("\n✅ Sprint 4 Matrix Pipeline execution stable. Ring buffer caching functional.")
    else:
        print("❌ Test failed: Motion tracking matrix miscalculated target entry.")

if __name__ == "__main__":
    run_motion_simulation()
