import cv2
import numpy as np

class TransientSignalFilter:
    def __init__(self, confidence_threshold=0.65):
        """
        Heuristic intelligence layer to separate orbital and meteor streaks
        from terrestrial contaminants (birds, bats, sensor noise).
        """
        self.confidence_threshold = confidence_threshold
        print("🧠 Heuristic Transient Signal Filter initialized.")

    def evaluate_motion_profile(self, processed_mask: np.ndarray, kinematic_data: dict) -> dict:
        """
        Analyzes the morphological structure of a motion detection mask to calculate
        a structural linearity confidence profile.
        
        :param processed_mask: The binary threshold/dilated mask from the motion tracker.
        :param kinematic_data: The metadata dictionary containing target bounding boxes.
        :returns: A dictionary with safety filtering parameters and final confidence rating.
        """
        if processed_mask is None or kinematic_data.get("active_target_count", 0) == 0:
            return {"confidence_score": 0.0, "classification": "NO_TARGET"}

        # 1. Use Hough Lines to measure geometric linearity
        # We look for straight lines formed by the moving object pixels
        lines = cv2.HoughLinesP(
            processed_mask, 
            rho=1, 
            theta=np.pi/180, 
            threshold=15, 
            minLineLength=10, 
            maxLineGap=5
        )

        line_count = len(lines) if lines is not None else 0
        
        # 2. Extract structural metrics from the tracking vector footprint
        # Satellites/Meteors have an elongated aspect ratio (high width-to-height or vice versa as a trail)
        vectors = kinematic_data.get("kinematic_vectors", [{}])[0]
        bbox = vector.get("bbox", (0, 0, 1, 1)) if 'vector' in locals() else vectors.get("bbox", (0, 0, 1, 1))
        _, _, w, h = bbox
        
        aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 1.0

        # 3. Dynamic Confidence Matrix Scoring Formula
        # Higher score if it has a distinct straight-line profile and an elongated trail structure
        base_score = 0.1
        if line_count > 0:
            base_score += 0.50  # Strongly weighs geometric linearity
        if aspect_ratio >= 2.0:
            base_score += 0.35  # Confirms a streak/trail shape footprint
            
        final_confidence = min(base_score, 1.0)

        # 4. Profile Classification Assignment
        if final_confidence >= self.confidence_threshold:
            if aspect_ratio > 4.0:
                classification = "METEOR_STREAK"
            else:
                classification = "SATELLITE_PASS"
        else:
            classification = "TERRESTRIAL_NOISE"  # Flagged as bird, insect, or wind artifact

        return {
            "confidence_score": round(final_confidence, 2),
            "line_segments_detected": line_count,
            "target_aspect_ratio": round(aspect_ratio, 2),
            "classification": classification,
            "pass_verified": bool(final_confidence >= self.confidence_threshold)
        }
