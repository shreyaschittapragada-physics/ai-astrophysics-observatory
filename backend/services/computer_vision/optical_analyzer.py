import cv2
import numpy as np
import os
import csv
from datetime import datetime

class OpticalIngestionEngine:
    def __init__(self, output_log="logs/optical_analysis_log.csv"):
        self.output_log = output_log
        
        # Configure a precise Star/Blob Detection parameter profile
        params = cv2.SimpleBlobDetector_Params()
        params.filterByColor = True
        params.blobColor = 255  # Look for bright targets on dark sky canvases
        params.filterByArea = True
        params.minArea = 2     # Minimum pixel radius for pinpoint stars
        params.maxArea = 150   # Prevents glares/clouds from being counted as stars
        params.filterByCircularity = False
        
        self.star_detector = cv2.SimpleBlobDetector_create(params)

    def process_image(self, image_path: str) -> dict:
        """Processes an ingested image file for sky metrics and stellar counts."""
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Image not found or corrupt at: {image_path}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        
        # 1. Slice Region of Interest (ROI) to remove edge artifacts
        roi = gray[int(h * 0.1):int(h * 0.9), int(w * 0.1):int(w * 0.9)]
        roi_blur = cv2.GaussianBlur(roi, (5, 5), 0)

        # 2. Extract Sky Brightness Metrics (Using your custom scale thresholds)
        mean_brightness = float(np.mean(roi_blur))
        std_brightness = float(np.std(roi_blur))

        if mean_brightness < 50:
            sky_quality = "Excellent"
        elif mean_brightness < 100:
            sky_quality = "Good"
        elif mean_brightness < 160:
            sky_quality = "Moderate"
        else:
            sky_quality = "Poor"

        # 3. Star Detection Engine
        # Threshold pushes stars into absolute white foreground against a dark canvas
        _, thresh = cv2.threshold(roi_blur, 40, 255, cv2.THRESH_BINARY)
        keypoints = self.star_detector.detect(thresh)
        star_count = len(keypoints)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        results = {
            "timestamp": timestamp,
            "filename": os.path.basename(image_path),
            "mean_brightness": round(mean_brightness, 3),
            "std_dev": round(std_brightness, 3),
            "sky_quality": sky_quality,
            "stars_detected": star_count
        }

        # 4. Write to CSV Log File
        self._log_to_csv(results)
        return results

    def _log_to_csv(self, data: dict):
        os.makedirs(os.path.dirname(self.output_log), exist_ok=True)
        file_exists = os.path.isfile(self.output_log)

        with open(self.output_log, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "filename", "mean_brightness", "std_dev", "sky_quality", "stars_detected"])
            writer.writerow([
                data["timestamp"], data["filename"], data["mean_brightness"], 
                data["std_dev"], data["sky_quality"], data["stars_detected"]
            ])
