import cv2
import numpy as np
import os
import datetime

class MotionTracker:
    def __init__(self, buffer_size=5):
        self.buffer = []
        self.prev_frame = None
        self.buffer_size = buffer_size

    def process(self, frame):
        # Update rolling buffer
        self.buffer.append(frame)
        if len(self.buffer) > self.buffer_size:
            self.buffer.pop(0)

        # Initialize previous frame
        if self.prev_frame is None:
            self.prev_frame = frame
            return False

        # Calculate difference
        diff = cv2.absdiff(self.prev_frame, frame)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        
        # Determine if motion exists
        motion_score = np.sum(thresh) / 255
        is_motion = motion_score > 50 
        
        if is_motion:
            self.save_motion_sequence()

        self.prev_frame = frame
        return is_motion

    def save_motion_sequence(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join("datasets", "captures", f"motion_{timestamp}")
        os.makedirs(save_path, exist_ok=True)
        for i, frame in enumerate(self.buffer):
            cv2.imwrite(os.path.join(save_path, f"frame_{i}.jpg"), frame)