import os
import json

class HorizonMaskEngine:
    def __init__(self, config_name="horizon_profile.json"):
        self.config_path = os.path.join(os.getcwd(), "backend", "config", config_name)
        # Default fallback profile: A step-function mapping Azimuth blocks to Minimum Elevation limits
        self.profile = {
            "0": 25.0,   # North: Tall trees/obstructions require > 25 degrees elevation
            "90": 15.0,  # East: Medium tree line
            "180": 10.0, # South: Clear skyline down to 10 degrees
            "270": 20.0  # West: Neighboring rooftop cutoff
        }
        self.load_profile()

    def load_profile(self):
        """Loads a custom horizon profile if it exists, otherwise creates a default one."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    raw_data = json.load(f)
                    # Convert keys back to integers for easy sector matching
                    self.profile = {int(k): float(v) for k, v in raw_data.items()}
                print("🛡️ Horizon Mask Engine: Custom obstruction profile loaded successfully.")
            except Exception as e:
                print(f"⚠️ Error loading horizon profile, using default matrix: {e}")
        else:
            self.save_profile()

    def save_profile(self):
        with open(self.config_path, "w") as f:
            json.dump(self.profile, f, indent=4)
        print("🛡️ Horizon Mask Engine: Default obstruction profile generated on disk.")

    def is_target_obstructed(self, azimuth: float, elevation: float) -> bool:
        """
        Evaluates current topocentric coordinates against the local obstruction map.
        Returns True if the target is physically blocked by structures.
        """
        # Normalize azimuth between 0 and 360
        az = azimuth % 360
        
        # Find the closest sector match in our step matrix
        available_sectors = sorted([int(k) for k in self.profile.keys()])
        matched_sector = available_sectors[0]
        
        for sector in available_sectors:
            if az >= sector:
                matched_sector = sector
            else:
                break
                
        min_required_elevation = self.profile[matched_sector]
        
        # If the satellite elevation is lower than the obstruction height, it's blocked
        return elevation < min_required_elevation
