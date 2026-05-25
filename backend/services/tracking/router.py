import os
import cv2
import numpy as np
from fastapi import APIRouter, HTTPException
from backend.services.tracking.iss_tracker import ISSTracker
from backend.services.cv_factory import CVObservationFactory

router = APIRouter(
    prefix="/api/v1/tracking",
    tags=["Orbital Tracking & Computer Vision"]
)

try:
    tracker = ISSTracker()
    cv_factory = CVObservationFactory()
except Exception as e:
    print(f"⚠️ Failed to initialize engines in router: {e}")
    tracker = None
    cv_factory = None

@router.get("/live")
async def get_live_telemetry():
    """
    Returns a unified hardware-telemetry payload.
    Combines live SGP4 look-angles with real-time camera frame CV analysis.
    """
    if not tracker or not cv_factory:
        raise HTTPException(status_code=500, detail="Core processing engines uninitialized.")
    
    try:
        # 1. Fetch live orbital tracking vectors from memory cache
        telemetry = tracker.calculate_relative_position()
        
        # 2. Mock or grab the current camera frame array (using your sky.jpg asset)
        image_path = os.path.join("datasets", "sky_images", "sky.jpg")
        if os.path.exists(image_path):
            frame = cv2.imread(image_path)
            # Run our refactored CV pipelines on the frame stream
            brightness = cv_factory.analyze_frame_brightness(frame)
            _, star_count = cv_factory.isolate_star_fields(frame)
            
            # 3. Append real-time visual metrics directly into the telemetry payload
            telemetry["optical_lens_profile"] = {
                "star_field_points_isolated": star_count,
                "sky_luminance_stats": brightness
            }
        else:
            telemetry["optical_lens_profile"] = {
                "status": "No active physical hardware/image stream detected at path."
            }
            
        return telemetry
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unified Core tracking pipeline error: {str(e)}")

@router.get("/predict")
async def get_pass_predictions():
    if not tracker:
        raise HTTPException(status_code=500, detail="Tracking engine is uninitialized.")
    return {
        "target": tracker.target,
        "observer_station": {"lat": tracker.lat, "lon": tracker.lon},
        "status": "Pass prediction scanning logic active",
        "upcoming_passes": []
    }
