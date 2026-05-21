from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.tracking.iss_tracker import SpaceTrackerEngine

router = APIRouter(prefix="/api", tags=["Satellite Observables Engine"])
tracker_engine = SpaceTrackerEngine(cache_hours=3)

class SatelliteTelemetryResponse(BaseModel):
    satellite_name: str
    latitude: float
    longitude: float
    altitude_km: float
    velocity_km_h: float
    timestamp: str

@router.get("/iss", response_model=SatelliteTelemetryResponse)
def get_legacy_iss_telemetry():
    try:
        return tracker_engine.get_satellite_position("iss")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/satellite/{name}", response_model=SatelliteTelemetryResponse)
def get_satellite_telemetry(name: str):
    try:
        return tracker_engine.get_satellite_position(name)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
