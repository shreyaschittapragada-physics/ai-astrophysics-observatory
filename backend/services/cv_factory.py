import cv2
import numpy as np
from datetime import datetime

class CVObservationFactory:
    def __init__(self, low_light_threshold=40.0):
        """
        Initializes the Computer Vision processing fabric for real-time sky frame ingestion.
        
        :param low_light_threshold: Maximum mean brightness before flag raising for city light pollution.
        """
        self.threshold = low_light_threshold
        print("👁️ Real-time Computer Vision Ingestion Factory initialized successfully.")

    def analyze_frame_brightness(self, frame: np.ndarray) -> dict:
        """
        Computes the statistical luminosity profiles of an ingested streaming frame.
        """
        if frame is None:
            return {"error": "Invalid or empty frame injected."}

        # Convert to Grayscale if the frame arrives in BGR/RGB format
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Calculate mean luminance across the pixel grid array
        mean_luminance = float(np.mean(gray))
        peak_luminance = float(np.max(gray))
        
        # Flags indicating if the field of view is compromised by clouds, moonlight, or city glare
        sky_compromised = bool(mean_luminance > self.threshold)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "mean_brightness": round(mean_luminance, 2),
            "peak_brightness": round(peak_luminance, 2),
            "sky_compromised_by_glare": sky_compromised
        }

    def isolate_star_fields(self, frame: np.ndarray, sensitivity_sigma=3.0) -> tuple:
        """
        Applies a high-pass threshold filter to isolate point-source star coordinates 
        from ambient atmospheric sky glows.
        
        :returns: A tuple containing (isolated_mask_frame, star_count)
        """
        if frame is None:
            return None, 0

        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Apply a localized Gaussian Blur to smooth out sensor thermal noise spikes
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Compute dynamic threshold values based on image standard deviation statistics
        mean, std_dev = cv2.meanStdDev(blurred)
        threshold_value = mean[0][0] + (sensitivity_sigma * std_dev[0][0])
        
        # Isolate pixels that pierce through the localized noise floor standard deviation
        _, star_mask = cv2.threshold(blurred, int(threshold_value), 255, cv2.THRESH_BINARY)
        
        # Find contours of isolated high-contrast point masks
        contours, _ = cv2.findContours(star_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by typical point-source structural properties (skipping large blurs)
        valid_star_count = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 1 <= area <= 50:  # Typical pixel spread profile of a clean background star
                valid_star_count += 1

        return star_mask, valid_star_count
