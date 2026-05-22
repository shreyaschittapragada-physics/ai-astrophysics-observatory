from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from backend.services.tracking.iss_tracker import ISSTracker

# Kept your original prefix and tags configuration intact
router = APIRouter(prefix="/api", tags=["Tracking"])

try:
    tracker = ISSTracker()
except Exception:
    tracker = None

# ==========================================
# PYDANTIC RESPONSE SCHEMAS
# ==========================================

class ISSTelemetryResponse(BaseModel):
    satellite_name: str
    latitude: float
    longitude: float
    altitude_km: float
    velocity_km_h: float
    timestamp: str

class LookAngles(BaseModel):
    elevation_deg: float
    azimuth_deg: float
    range_km: float
    is_above_horizon: bool

class LiveTrackingResponse(BaseModel):
    telemetry: ISSTelemetryResponse
    look_angles: LookAngles

class PassPrediction(BaseModel):
    rise_time: str
    max_elevation_deg: float
    peak_azimuth_deg: float
    set_time: str

class PredictionResponse(BaseModel):
    observer_latitude: float
    observer_longitude: float
    total_passes_found: int
    upcoming_passes: List[PassPrediction]


# ==========================================
# HELPER FOR TRACKER LIFECYCLE
# ==========================================
def verify_tracker():
    """Keeps your original lazy-loading failover strategy working safely."""
    global tracker
    if tracker is None:
        try:
            tracker = ISSTracker()
        except Exception:
            raise HTTPException(status_code=503, detail="Tracking engine unavailable")
    return tracker


# ==========================================
# API ENDPOINTS
# ==========================================

@router.get("/iss", response_model=ISSTelemetryResponse)
def get_iss_telemetry():
    """Your original endpoint: returns pure global coordinate telemetry."""
    active_tracker = verify_tracker()
    try:
        return active_tracker.get_current_position()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/iss/live", response_model=LiveTrackingResponse)
def get_live_coordinate_tracking(
    lat: float = Query(17.385, description="Observer Ground Latitude"),
    lon: float = Query(78.486, description="Observer Ground Longitude"),
    alt: float = Query(542.0, description="Observer Ground Elevation Altitude in Meters")
):
    """New Endpoint: Computes live local Azimuth and Elevation look angles."""
    active_tracker = verify_tracker()
    try:
        position = active_tracker.get_current_position()
        look_angles = active_tracker.get_look_angles(lat, lon, alt)
        return {
            "telemetry": position,
            "look_angles": look_angles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/iss/predictions", response_model=PredictionResponse)
def get_pass_predictions_forecast(
    lat: float = Query(17.385, description="Observer Ground Latitude"),
    lon: float = Query(78.486, description="Observer Ground Longitude"),
    alt: float = Query(542.0, description="Observer Ground Elevation Altitude in Meters"),
    days: int = Query(7, ge=1, le=14, description="Forecast limit window window")
):
    """New Endpoint: Returns a 7-day predictive timeline of overhead passes."""
    active_tracker = verify_tracker()
    try:
        passes = active_tracker.compute_future_passes(lat, lon, alt, days)
        return {
            "observer_latitude": lat,
            "observer_longitude": lon,
            "total_passes_found": len(passes),
            "upcoming_passes": passes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))