import cv2
import os
from datetime import datetime
from collections import deque

class MotionTracker:
    def __init__(self, buffer_size=30, sensitivity=5000):
        self.buffer = deque(maxlen=buffer_size)
        self.sensitivity = sensitivity
        self.last_frame = None
        self.save_dir = "captures"
        os.makedirs(self.save_dir, exist_ok=True)

    def process(self, frame):
        # 1. Update Buffer (always keep the last 'buffer_size' frames)
        self.buffer.append(frame)
        
        # 2. Motion Detection (using Grayscale + Gaussian Blur to reduce noise)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        report = {"motion_detected": False, "metadata": {"saved_path": None}}

        if self.last_frame is None:
            self.last_frame = gray
            return report

        # Compare current frame with the last known frame
        frame_delta = cv2.absdiff(self.last_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        self.last_frame = gray

        # 3. Detect movement
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            if cv2.contourArea(contour) > self.sensitivity:
                report["motion_detected"] = True
                report["metadata"]["saved_path"] = self.save_buffer()
                break
        
        return report

    def save_buffer(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.save_dir, f"capture_{timestamp}.avi")
        
        # Write buffer to disk
        height, width, layers = self.buffer[0].shape
        out = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'XVID'), 10, (width, height))
        for frame in self.buffer:
            out.write(frame)
        out.release()
        return filename
