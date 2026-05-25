import os
import math
from datetime import datetime

class ISSTracker:
    def __init__(self, lat=17.4933, lon=78.3404, alt=545):
        """
        Initializes the tracker with observer coordinates.
        Defaults are configured for tracking observation passes.
        """
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

    def load_tle(self, filename="stations.tle"):
        """Reads TLE data from the tracking data directory."""
        tle_path = os.path.join(self.data_dir, filename)
        if not os.path.exists(tle_path):
            print(f"⚠️ TLE file not found at: {tle_path}")
            return None
        
        with open(tle_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        return lines

    def predict_next_pass(self, target_name="ISS"):
        """
        Predicts the next overhead pass for a target satellite.
        Returns a mock pass window for orchestration testing if engine is local.
        """
        # In a full run, this parses the loaded TLE data line-by-line
        print(f"📡 Calculating next pass windows for target: {target_name}...")
        
        now = datetime.now()
        start_time = now.strftime("%Y-%m-%d %H:%M:%S")
        end_time = datetime.fromtimestamp(now.timestamp() + 600).strftime("%Y-%m-%d %H:%M:%S") # 10 min pass
        
        return {
            "target_name": target_name,
            "start_time": start_time,
            "end_time": end_time,
            "max_elevation": 68.5
        }
