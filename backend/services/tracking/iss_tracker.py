import os, time, requests, ijson
from datetime import timedelta
from skyfield.api import EarthSatellite, load

class ISSTracker:
    def __init__(self):
        self.ts = load.timescale()
        self.full_catalog = {}
        self.data_file = "satellites.json"
        self.cv = "ACTIVE_MONITORING"
        self._ensure_data_freshness()
        self.load_catalog()

    def _ensure_data_freshness(self):
        if not os.path.exists(self.data_file) or (time.time() - os.path.getmtime(self.data_file) > 86400):
            try:
                self._download_catalog()
            except Exception as e:
                print(f"⚠️ Catalog refresh failed ({e}). Falling back to cached local file.")

    def _download_catalog(self):
        user = os.getenv("SPACE_TRACK_USER")
        pwd = os.getenv("SPACE_TRACK_PASS")
        if not user or not pwd:
            raise ValueError("Space-Track credentials missing from environment.")
        
        session = requests.Session()
        session.post("https://www.space-track.org/ajaxauth/login", data={'identity': user, 'password': pwd})
        url = "https://www.space-track.org/basicspacedata/query/class/gp/decay_date/null-val/epoch/%3Enow-10/format/json"
        resp = session.get(url)
        resp.raise_for_status()
        
        with open(self.data_file, "w", encoding="utf-8") as f:
            f.write(resp.text)

    def load_catalog(self):
        self.full_catalog = {} 
        if not os.path.exists(self.data_file):
            print("⚠️ No satellite data found locally.")
            return
            
        with open(self.data_file, "rb") as f:
            for entry in ijson.items(f, 'item'):
                try:
                    sat = EarthSatellite.from_omm(self.ts, entry)
                    self.full_catalog[sat.name] = sat
                except Exception:
                    continue
        print(f"✓ Brain Ready: {len(self.full_catalog)} satellites indexed.")

    def get_position(self, name, minutes_ahead=0):
        sat = self.full_catalog.get(name)
        if not sat: return None
        time_point = self.ts.now() + timedelta(minutes=minutes_ahead)
        geocentric = sat.at(time_point)
        subpoint = geocentric.subpoint()
        return {
            "name": name,
            "lat": subpoint.latitude.degrees,
            "lon": subpoint.longitude.degrees,
            "alt_km": subpoint.elevation.km,
            "timestamp": time_point.utc_iso()
        }
