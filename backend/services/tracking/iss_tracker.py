import datetime
import os
from skyfield.api import Loader

class SpaceTrackerEngine:
    def __init__(self, cache_hours: int = 3):
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.loader = Loader(self.data_dir, verbose=False)
        self.ts = self.loader.timescale()
        
        self.cache_hours = cache_hours
        self.satellite_mappings = {
            "iss": "ISS (ZARYA)",
            "hubble": "HST",
            "noaa": "NOAA 19",
            "starlink": "STARLINK"
        }
        
        self.satellites_cache = {}
        self._initialize_database()

    def _initialize_database(self):
        urls = {
            "stations": "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle",
            "science": "https://celestrak.org/NORAD/elements/gp.php?GROUP=science&FORMAT=tle",
            "weather": "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle",
            "starlink": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle"
        }

        for group, url in urls.items():
            try:
                filename = f"{group}.tle"
                filepath = os.path.join(self.data_dir, filename)
                
                force_reload = True
                if os.path.exists(filepath):
                    days_limit = self.cache_hours / 24.0
                    if self.loader.days_old(filename) < days_limit:
                        force_reload = False
                
                # loader.tle_file returns a LIST of EarthSatellite objects
                sats_list = self.loader.tle_file(url, filename=filename, reload=force_reload)
                
                # Loop through the list and index them by name inside our cache dictionary
                for sat in sats_list:
                    self.satellites_cache[sat.name.strip()] = sat
                    
            except Exception as e:
                print(f"?? Error processing TLE cache group '{group}': {e}")

    def get_satellite_position(self, satellite_slug: str):
        slug = satellite_slug.lower()
        if slug not in self.satellite_mappings:
            raise ValueError(f"Satellite '{satellite_slug}' not supported.")
            
        target_name = self.satellite_mappings[slug]
        satellite = None
        for name in self.satellites_cache:
            if target_name in name:
                satellite = self.satellites_cache[name]
                target_name = name
                break
                
        if not satellite:
            raise ValueError(f"TLE data for '{target_name}' not found in cache layer.")

        now = self.ts.now()
        geocentric = satellite.at(now)
        subpoint = geocentric.subpoint()
        
        velocity_vector = geocentric.velocity.km_per_s
        speed_km_s = (velocity_vector[0]**2 + velocity_vector[1]**2 + velocity_vector[2]**2)**0.5
        speed_km_h = speed_km_s * 3600

        return {
            "satellite_name": target_name,
            "latitude": round(subpoint.latitude.degrees, 4),
            "longitude": round(subpoint.longitude.degrees, 4),
            "altitude_km": round(subpoint.elevation.km, 2),
            "velocity_km_h": round(speed_km_h, 2),
            "timestamp": datetime.datetime.now().isoformat()
        }

class ISSTracker(SpaceTrackerEngine):
    def get_current_position(self):
        return self.get_satellite_position("iss")
