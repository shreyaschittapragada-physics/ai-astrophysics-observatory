import json
import os
import urllib.request
from datetime import datetime
from skyfield.api import Topos, load
from skyfield.sgp4lib import EarthSatellite
from sgp4.api import Satrec, WGS72

class ISSTracker:
    def __init__(self, config_path="config.json"):
        base_dir = os.getcwd()
        self.config_file = os.path.join(base_dir, config_path)
        
        try:
            with open(self.config_file, 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
            print(f"🎯 Successfully loaded configurations from: {self.config_file}")
        except Exception as e:
            print(f"⚠️ Internal Reading Error: {str(e)}")
            config = {}

        observer = config.get("observer", {})
        tracking = config.get("tracking", {})

        self.lat = observer.get("latitude", 17.4933)
        self.lon = observer.get("longitude", 78.3404)
        self.alt = observer.get("elevation_meters", 545.0)
        self.target = tracking.get("selected_target", "ISS")
        self.horizon_limit = tracking.get("horizon_cutoff_degrees", 10.0)

        self.ts = load.timescale()
        self.station_location = Topos(latitude_degrees=self.lat, longitude_degrees=self.lon, elevation_m=self.alt)
        
        # In-memory cache for the EarthSatellite instance
        self._cached_satellite = None
        self.last_updated = None

    def fetch_and_cache_tle(self):
        """Fetches live orbital parameters and caches the EarthSatellite object in memory"""
        try:
            url = 'https://celestrak.org/NORAD/elements/visual.txt'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                lines = [line.decode('utf-8').strip() for line in response.readlines()]
            
            for line in lines:
                if not line or "," not in line:
                    continue
                
                parts = line.split(',')
                name = parts[0]
                catalog_id = parts[11] if len(parts) > 11 else ""
                
                if self.target.upper() in name.upper() or catalog_id == "25544":
                    print(f"📡 Worker refreshed OMM metrics for: {name}")
                    
                    epoch_str = parts[2]
                    dt = datetime.strptime(epoch_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                    
                    from math import radians
                    satrec = Satrec()
                    mean_motion_rad_min = float(parts[3]) * 2.0 * 3.141592653589793 / 1440.0
                    
                    satrec.sgp4init(
                        WGS72, 'i', int(catalog_id if catalog_id.isdigit() else 25544),
                        (dt - datetime(1949, 12, 31)).days,
                        (dt.hour * 3600 + dt.minute * 60 + dt.second) / 86400.0,
                        float(parts[4]), 0.0, float(parts[9]),
                        radians(float(parts[7])), radians(float(parts[5])), radians(float(parts[8])),
                        mean_motion_rad_min, radians(float(parts[6])),
                    )
                    
                    self._cached_satellite = EarthSatellite.from_satrec(satrec, self.ts)
                    self.last_updated = datetime.utcnow()
                    return True
                    
            raise ValueError(f"Target '{self.target}' not found in active dataset.")
        except Exception as e:
            print(f"⚠️ Background Refresh Failure: {e}. Keeping existing or fallback profiles.")
            if not self._cached_satellite:
                line1 = "1 25544U 98067A   26145.52083333  .00016717  00000-0  30142-3 0  9997"
                line2 = "2 25544  51.6412  15.2341 0001470  89.3412  32.1147 15.49812345421115"
                self._cached_satellite = EarthSatellite(line1, line2, self.target, self.ts)
            return False

    def calculate_relative_position(self):
        # Fallback to direct generation if cache is completely empty
        if not self._cached_satellite:
            self.fetch_and_cache_tle()
            
        t = self.ts.now()
        difference = self._cached_satellite - self.station_location
        topocentric = difference.at(t)
        alt, az, distance = topocentric.altaz()
        
        current_elevation = alt.degrees
        current_azimuth = az.degrees
        range_km = distance.km
        
        is_visible = bool(current_elevation >= self.horizon_limit)
        horizon_status = "ABOVE HORIZON" if is_visible else "BELOW HORIZON"
        
        return {
            "target": self.target,
            "last_cache_update": self.last_updated.isoformat() if self.last_updated else "Using Default Vectors",
            "observer_coordinates": {"lat": self.lat, "lon": self.lon, "alt_m": self.alt},
            "calculated_look_angles": {
                "elevation_deg": round(current_elevation, 4),
                "azimuth_deg": round(current_azimuth, 4),
                "slant_range_km": round(range_km, 2)
            },
            "horizon_status": horizon_status,
            "capture_authorized": is_visible
        }
