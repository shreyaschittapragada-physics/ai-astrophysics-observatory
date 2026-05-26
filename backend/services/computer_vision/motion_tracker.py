import cv2
import numpy as np
from collections import deque
import os
import time

class TransientMotionDetector:
    def __init__(self, buffer_size=30, min_contour_area=25):
        # MOG2 Subtractor configured for highly variable atmospheric layouts
        self.back_sub = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=25, detectShadows=False)
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        
        # Volatile RAM rolling buffer to capture pre-motion event context frames
        self.frame_buffer = deque(maxlen=buffer_size)
        self.min_contour_area = min_contour_area
        self.cooldown_counter = 0

    def process_stream_frame(self, frame):
        """Processes a continuous video frame input, tracking rolling temporal changes."""
        if frame is None:
            return False, {}, None

        # Convert to grayscale for raw pixel matrix calculations
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame.copy()

        # Append current frame to volatile pre-motion context memory
        self.frame_buffer.append(gray)
        
        # Apply temporal frame-differencing background subtraction
        fg_mask = self.back_sub.apply(gray)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, self.kernel)
        
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        largest_area = 0
        kinematic_vectors = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > self.min_contour_area:
                motion_detected = True
                if area > largest_area:
                    largest_area = area
                
                x, y, w, h = cv2.boundingRect(cnt)
                kinematic_vectors.append({
                    "bbox": (x, y, w, h),
                    "centroid": (int(x + w/2), int(y + h/2)),
                    "area": area
                })

        # Provide a safe structural default if no coordinates are isolated
        if not kinematic_vectors:
            kinematic_vectors.append({"bbox": (0, 0, 1, 1), "centroid": (0, 0), "area": 0})

        metadata = {
            "active_target_count": len(kinematic_vectors) if motion_detected else 0,
            "kinematic_vectors": kinematic_vectors,
            "largest_contour_area": largest_area,
            "timestamp": time.time()
        }

        return motion_detected, metadata, fg_mask

    def dump_context_sequence(self, event_id: str):
        """Dumps the pre-motion volatile memory buffer to disk when an anomaly triggers."""
        save_path = os.path.join("datasets", "captures", f"event_{event_id}")
        os.makedirs(save_path, exist_ok=True)
        for i, f in enumerate(self.frame_buffer):
            cv2.imwrite(os.path.join(save_path, f"frame_{i:02d}.jpg"), f)
        return save_path
