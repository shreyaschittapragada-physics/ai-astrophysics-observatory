from fastapi import APIRouter, HTTPException
from backend.services.tracking.iss_tracker import ISSTracker

# Initialize the router with a clean API prefix group
router = APIRouter(
    prefix="/api/v1/tracking",
    tags=["Orbital Tracking"]
)

try:
    # Instantiate the tracking physics engine
    tracker = ISSTracker()
except Exception as e:
    print(f"⚠️ Failed to initialize ISSTracker in router: {e}")
    tracker = None

@router.get("/live")
async def get_live_telemetry():
    """
    Fetches real-time horizontal coordinates (Az/El) and horizon visibility status
    calculated dynamically from live Celestrak OMM orbital metrics.
    """
    if not tracker:
        raise HTTPException(status_code=500, detail="Tracking engine is uninitialized.")
    
    try:
        telemetry = tracker.calculate_relative_position()
        return telemetry
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Telemetry generation error: {str(e)}")

@router.get("/predict")
async def get_pass_predictions():
    """
    Placeholder endpoint for upcoming orbital pass predictions.
    Will scan forward vectors to compute local horizon crossing windows.
    """
    if not tracker:
        raise HTTPException(status_code=500, detail="Tracking engine is uninitialized.")
    
    return {
        "target": tracker.target,
        "observer_station": {"lat": tracker.lat, "lon": tracker.lon},
        "status": "Pass prediction scanning logic active",
        "upcoming_passes": []
    }
