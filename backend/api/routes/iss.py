from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.tracking.iss_tracker import ISSTracker

router = APIRouter(prefix="/api", tags=["Tracking"])

try:
    tracker = ISSTracker()
except Exception as e:
    tracker = None

class ISSTelemetryResponse(BaseModel):
    satellite_name: str
    latitude: float
    longitude: float
    altitude_km: float
    velocity_km_h: float
    timestamp: str

@router.get("/iss", response_model=ISSTelemetryResponse)
def get_iss_telemetry():
    global tracker
    if tracker is None:
        try:
            tracker = ISSTracker()
        except Exception:
            raise HTTPException(status_code=503, detail="Tracking engine unavailable")
    try:
        return tracker.get_current_position()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))