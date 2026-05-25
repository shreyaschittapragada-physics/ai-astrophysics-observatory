import cv2
import numpy as np
from collections import deque
from datetime import datetime

class TransientMotionDetector:
    def __init__(self, buffer_size=30, min_contour_area=15, threshold_sens=25):
        """
        High-throughput kinematic motion tracking engine for transient sky phenomena.
        
        :param buffer_size: Number of pre-motion context frames to retain in memory.
        :param min_contour_area: Minimum pixel area to trigger tracking (filters tiny sensor noise).
        :param threshold_sens: Sensitivity of the frame-differencing absolute delta threshold.
        """
        self.min_area = min_contour_area
        self.threshold_sens = threshold_sens
        
        # Ring buffer for pre-motion context frames
        self.frame_buffer = deque(maxlen=buffer_size)
        
        # Background subtractor initialization for adaptive structural learning
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=16, detectShadows=False)
        
        self.is_tracking = False
        print("🚀 Kinematic Motion Tracker & Ring Buffer initialized successfully.")

    def process_frame(self, frame: np.ndarray) -> tuple:
        """
        Processes an incoming streaming frame matrix.
        
        :param frame: Grayscale or BGR NumPy frame array.
        :returns: A tuple of (is_motion_detected, motion_metadata_dict, processed_mask)
        """
        if frame is None:
            return False, {}, None

        # Ensure grayscale conversion for matrix delta operations
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # 1. Append raw frame copy to the rolling pre-motion context ring buffer
        self.frame_buffer.append(gray.copy())

        # 2. Apply history-based background subtraction matrix
        fg_mask = self.bg_subtractor.apply(gray)
        
        # 3. Morphological filtering to clean up isolated single-pixel atmospheric scintillation
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated_mask = cv2.dilate(fg_mask, kernel, iterations=1)

        # 4. Extract motion vectors / contours
        contours, _ = cv2.findContours(dilated_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        active_vectors = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= self.min_area:
                motion_detected = True
                # Extract structural bounding dimensions of the moving target
                x, y, w, h = cv2.boundingRect(cnt)
                centroid_x = int(x + w / 2)
                centroid_y = int(y + h / 2)
                
                active_vectors.append({
                    "centroid": (centroid_x, centroid_y),
                    "bbox": (x, y, w, h),
                    "pixel_area": float(area)
                })

        # Update tracking flags state transitions
        self.is_tracking = motion_detected

        metadata = {
            "timestamp": datetime.utcnow().isoformat(),
            "motion_triggered": motion_detected,
            "active_target_count": len(active_vectors),
            "kinematic_vectors": active_vectors,
            "buffered_context_frames": len(self.frame_buffer)
        }

        return motion_detected, metadata, dilated_mask
