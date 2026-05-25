import asyncio
from datetime import datetime, timedelta, timezone
import os
import sys
import numpy as np
import cv2

sys.path.append(os.getcwd())

from backend.services.database.db_manager import DatabaseManager
from backend.services.computer_vision.motion_tracker import TransientMotionDetector
from backend.services.computer_vision.meteor_filter import TransientSignalFilter

class ObservatoryAutomationDaemon:
    def __init__(self, check_interval_seconds=1):
        self.check_interval = check_interval_seconds
        self.db = DatabaseManager()
        
        # Core V2 Vision & Intelligence Subsystems Interlocked here
        self.tracker = TransientMotionDetector(buffer_size=10, min_contour_area=15)
        self.intelligence_filter = TransientSignalFilter(confidence_threshold=0.65)
        
        self.is_running = False
        self.current_state = "IDLE"
        
        # Setup an immediate timetable event for a live camera processing verification pass
        self.pass_timetable = [
            {
                "target": "ISS (ZARYA)",
                "aos": datetime.now(timezone.utc) + timedelta(seconds=2),
                "los": datetime.now(timezone.utc) + timedelta(seconds=12)
            }
        ]
        print("🤖 Autonomous Edge Interlocking Daemon Online.")

    async def start_orchestration_loop(self):
        self.is_running = True
        print("⏰ Hardware orchestration loop scanning timetable targets...\n")
        
        while self.is_running:
            now = datetime.now(timezone.utc)
            
            for execution_pass in list(self.pass_timetable):
                target = execution_pass["target"]
                aos = execution_pass["aos"]
                los = execution_pass["los"]
                
                # 1. State Shift: ARMED
                if now < aos and (aos - now).total_seconds() <= 5 and self.current_state == "IDLE":
                    self.current_state = "ARMED"
                    print(f"🚨 [STATE: ARMED] {target} incoming. Pre-allocating context frame arrays...")
                    # Seed background history buffer with clear static sky frames
                    for _ in range(10):
                        self.tracker.process_frame(np.zeros((500, 500), dtype=np.uint8))
                
                # 2. State Shift: RECORDING (Processing CV Streams)
                elif aos <= now <= los:
                    if self.current_state != "RECORDING":
                        self.current_state = "RECORDING"
                        print(f"📸 [STATE: RECORDING] {target} overhead. Interlocking optical vision matrices...")
                    
                    # Generate a clean, real moving meteor streak across the lens array during the tracking sweep
                    simulated_sky_frame = np.zeros((500, 500), dtype=np.uint8)
                    cv2.line(simulated_sky_frame, (10, 200), (490, 210), 255, 2)
                    
                    # Pass raw frames directly into your V2 processing pipeline
                    motion_detected, metadata, processed_mask = self.tracker.process_frame(simulated_sky_frame)
                    
                    if motion_detected:
                        analysis = self.intelligence_filter.evaluate_motion_profile(processed_mask, metadata)
                        if analysis["pass_verified"] and now.second % 4 == 0:  # Avoid logging duplicates on every frame tick
                            print(f"   🎯 Intercepted high-confidence transient: {analysis['classification']} ({analysis['confidence_score']*100}%)")
                            self.db.log_detection_event(
                                classification=analysis["classification"],
                                confidence=analysis["confidence_score"],
                                lines=analysis["line_segments_detected"],
                                aspect_ratio=analysis["target_aspect_ratio"],
                                frame_path="captures/daemon_intercept.jpg"
                            )
                
                # 3. State Shift: IDLE
                elif now > los and self.current_state == "RECORDING":
                    self.current_state = "IDLE"
                    print(f"💤 [STATE: IDLE] {target} pass completed. Releasing frame hardware matrices back to standby power.\n")
                    self.pass_timetable.remove(execution_pass)
            
            await asyncio.sleep(self.check_interval)

    def stop(self):
        self.is_running = False
        print("🛑 Edge automation system closed safely.")

async def main():
    daemon = ObservatoryAutomationDaemon(check_interval_seconds=1)
    try:
        await asyncio.wait_for(daemon.start_orchestration_loop(), timeout=16.0)
    except TimeoutError:
        daemon.stop()

if __name__ == "__main__":
    asyncio.run(main())
