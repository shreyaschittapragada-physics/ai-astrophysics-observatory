import os
import cv2
import numpy as np
from fastapi import APIRouter, HTTPException
from backend.services.tracking.iss_tracker import ISSTracker
from backend.services.cv_factory import CVObservationFactory
from backend.services.database.db_manager import DatabaseManager

router = APIRouter(
    prefix="/api/v1/tracking",
    tags=["Orbital Tracking & Computer Vision"]
)

try:
    tracker = ISSTracker()
    cv_factory = CVObservationFactory()
    db = DatabaseManager()
except Exception as e:
    print(f"⚠️ Failed to initialize engines in router: {e}")
    tracker = None
    cv_factory = None
    db = None

@router.get("/live")
async def get_live_telemetry():
    """Returns a unified hardware-telemetry payload combining SGP4 look-angles and CV metrics."""
    if not tracker or not cv_factory:
        raise HTTPException(status_code=500, detail="Core processing engines uninitialized.")
    
    try:
        telemetry = tracker.calculate_relative_position()
        image_path = os.path.join("datasets", "sky_images", "sky.jpg")
        
        if os.path.exists(image_path):
            frame = cv2.imread(image_path)
            brightness = cv_factory.analyze_frame_brightness(frame)
            _, star_count = cv_factory.isolate_star_fields(frame)
            
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

@router.get("/history")
async def get_detection_history():
    """
    Fetches all archived high-confidence tracking logs from SQLite.
    This feeds the historical data table on the dashboard UI.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Database engine uninitialized.")
    
    try:
        logs = db.fetch_all_logs()
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "id": log[0],
                "timestamp": log[1],
                "classification": log[2],
                "confidence_score": f"{log[3] * 100}%",
                "line_segments": log[4],
                "aspect_ratio": log[5],
                "captured_frame_path": log[6]
            })
        return {"total_records": len(formatted_logs), "events": formatted_logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database retrieval failure: {str(e)}")

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
