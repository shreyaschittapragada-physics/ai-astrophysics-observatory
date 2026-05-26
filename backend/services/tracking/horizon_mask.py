import os
import json

class HorizonMaskEngine:
    def __init__(self, config_name="horizon_profile.json"):
        self.config_path = os.path.join(os.getcwd(), "backend", "config", config_name)
        self.profile = {
            0: 25.0,   # North
            90: 15.0,  # East
            180: 10.0, # South
            270: 20.0  # West
        }
        self.load_profile()

    def load_profile(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    raw_data = json.load(f)
                    # Force keys to be integers natively
                    self.profile = {int(k): float(v) for k, v in raw_data.items()}
                print("🛡️ Horizon Mask Engine: Custom obstruction profile loaded successfully.")
            except Exception as e:
                print(f"⚠️ Error loading horizon profile, using default matrix: {e}")
        else:
            self.save_profile()

    def save_profile(self):
        with open(self.config_path, "w") as f:
            json.dump(self.profile, f, indent=4)
        print("🛡️ Horizon Mask Engine: Fallback profile matrix generated on disk.")

    def is_target_obstructed(self, azimuth: float, elevation: float) -> bool:
        az = azimuth % 360
        available_sectors = sorted([int(k) for k in self.profile.keys()])
        matched_sector = available_sectors[0]
        
        for sector in available_sectors:
            if az >= sector:
                matched_sector = sector
            else:
                break
                
        min_required_elevation = self.profile[matched_sector]
        return elevation < min_required_elevation
