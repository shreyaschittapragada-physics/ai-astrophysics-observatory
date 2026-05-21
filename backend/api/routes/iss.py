from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from backend.services.tracking.iss_tracker import SpaceTrackerEngine

router = APIRouter(prefix="/api", tags=["Satellite Observables Engine"])
tracker_engine = SpaceTrackerEngine(cache_hours=3)

class AstronomyMetrics(BaseModel):
    observer_latitude: float
    observer_longitude: float
    local_altitude_deg: float
    local_azimuth_deg: float
    right_ascension_hours: float
    declination_degrees: float

class SatelliteTelemetryResponse(BaseModel):
    satellite_name: str
    latitude: float
    longitude: float
    altitude_km: float
    velocity_km_h: float
    timestamp: str
    astronomy_data: Optional[AstronomyMetrics] = None

@router.get("/iss", response_model=SatelliteTelemetryResponse)
def get_legacy_iss_telemetry():
    try:
        return tracker_engine.get_satellite_position("iss")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/satellite/{name}", response_model=SatelliteTelemetryResponse)
def get_satellite_telemetry(
    name: str,
    obs_lat: Optional[float] = Query(None, description="Observer latitude in decimal degrees"),
    obs_lon: Optional[float] = Query(None, description="Observer longitude in decimal degrees"),
    obs_alt: Optional[float] = Query(0.0, description="Observer altitude above sea level in meters")
):
    try:
        return tracker_engine.get_satellite_position(name, obs_lat, obs_lon, obs_alt)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
