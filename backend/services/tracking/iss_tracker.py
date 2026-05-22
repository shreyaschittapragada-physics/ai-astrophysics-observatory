import os
import datetime
import urllib.request
from skyfield.api import load, wgs84, EarthSatellite

class ISSTracker:
    def __init__(self):
        self.ts = load.timescale()
        self.cache_dir = os.path.join(os.getcwd(), "backend", "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Mapping CelesTrak NORAD IDs for live downloads
        self.satellite_ids = {
            "iss": {"id": "25544", "name": "ISS (ZARYA)"},
            "tiangong": {"id": "48274", "name": "TIANGONG (CSS)"},
            "hubble": {"id": "20580", "name": "HUBBLE SPACE TELESCOPE"}
        }

    def _get_live_tle(self, sat_key: str):
        """Fetches live TLE from CelesTrak or reads from local cache if fresh."""
        sat_info = self.satellite_ids.get(sat_key.lower(), self.satellite_ids["iss"])
        cache_file = os.path.join(self.cache_dir, f"{sat_key}_tle.txt")
        
        # Check if cache file exists and is less than 24 hours old
        if os.path.exists(cache_file):
            file_age = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(cache_file))
            if file_age.total_seconds() < 86400:
                with open(cache_file, "r") as f:
                    lines = f.read().splitlines()
                if len(lines) >= 2:
                    return lines[0], lines[1], sat_info["name"]

        # Fetch fresh data from CelesTrak if cache expired or missing
        try:
            url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={sat_info['id']}&FORMAT=TLE"
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8').splitlines()
            
            if len(content) >= 3:
                l1, l2 = content[1].strip(), content[2].strip()
                with open(cache_file, "w") as f:
                    f.write(f"{l1}\n{l2}")
                return l1, l2, sat_info["name"]
        except Exception as e:
            print(f"TLE network fetch failed, using internal fallback: {e}")
            
        # Resilient fallback profiles if internet is down
        fallbacks = {
            "iss": ("1 25544U 98067A   26142.22818981  .00014022  00000-0  24996-3 0  9993", "2 25544  51.6418 132.8831 0001819  86.1343  51.7820 15.49520847568551"),
            "tiangong": ("1 48274U 21035A   26142.16480434  .00011537  00000-0  13511-3 0  9997", "2 48274  41.4721 154.5512 0001928  62.1147 288.1130 15.59765231284710"),
            "hubble": ("1 20580U 90037B   26141.80211568  .00002104  00000-0  14502-3 0  9998", "2 20580  28.4681  22.1145 0002419 114.1512 281.1415 15.06411512961120")
        }
        l1, l2 = fallbacks.get(sat_key.lower(), fallbacks["iss"])
        return l1, l2, sat_info["name"]

    def get_satellite_object(self, key: str):
        l1, l2, name = self._get_live_tle(key)
        return EarthSatellite(l1, l2, name, self.ts), name

    def get_current_position(self, sat_key: str = "iss"):
        sat, sat_name = self.get_satellite_object(sat_key)
        now = self.ts.now()
        geocentric = sat.at(now)
        subpoint = geocentric.subpoint()
        
        velocity_vector = geocentric.velocity.km_per_s
        speed_km_h = (velocity_vector[0]**2 + velocity_vector[1]**2 + velocity_vector[2]**2)**0.5 * 3600

        return {
            "satellite_name": sat_name,
            "latitude": round(subpoint.latitude.degrees, 4),
            "longitude": round(subpoint.longitude.degrees, 4),
            "altitude_km": round(subpoint.elevation.km, 2),
            "velocity_km_h": round(speed_km_h, 2),
            "timestamp": datetime.datetime.now().isoformat()
        }

    def get_look_angles(self, sat_key: str, lat: float, lon: float, alt_m: float):
        sat, _ = self.get_satellite_object(sat_key)
        now = self.ts.now()
        observer = wgs84.latlon(lat, lon, elevation_m=alt_m)
        topocentric = (sat - observer).at(now)
        alt, az, distance = topocentric.altaz()
        
        return {
            "elevation_deg": round(alt.degrees, 2),
            "azimuth_deg": round(az.degrees, 2),
            "range_km": round(distance.km, 2),
            "is_above_horizon": alt.degrees > 0
        }

    def compute_future_passes(self, sat_key: str, lat: float, lon: float, alt_m: float, days: int = 7):
        """Computes all visible overflight vectors for the target station coordinates."""
        sat, _ = self.get_satellite_object(sat_key)
        observer = wgs84.latlon(lat, lon, elevation_m=alt_m)
        
        t0 = self.ts.now()
        t1 = self.ts.utc(t0.utc_datetime() + datetime.timedelta(days=days))
        
        # Find horizon crossings (min elevation threshold 10 degrees for clear visibility)
        times, events = sat.find_events(observer, t0, t1, altitude_degrees=10.0)
        
        passes = []
        current_pass = {}
        
        for t, event in zip(times, events):
            # Event 0: Rise, 1: Peak Culmination, 2: Set
            if event == 0:
                current_pass = {"rise_time": t.utc_datetime().isoformat() + "Z"}
            elif event == 1 and current_pass:
                topocentric = (sat - observer).at(t)
                alt, az, _ = topocentric.altaz()
                current_pass["max_elevation_deg"] = round(alt.degrees, 1)
                current_pass["peak_azimuth_deg"] = round(az.degrees, 1)
            elif event == 2 and current_pass:
                current_pass["set_time"] = t.utc_datetime().isoformat() + "Z"
                passes.append(current_pass)
                current_pass = {}
                
        return passes[:5] # Return next 5 clean passes
