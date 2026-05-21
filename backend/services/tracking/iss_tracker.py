import datetime
from skyfield.api import load, EarthSatellite

class ISSTracker:
    def __init__(self):
        self.ts = load.timescale()
        self.line1 = "1 25544U 98067A   26141.21855671  .00014281  00000-0  25427-3 0  9997"
        self.line2 = "2 25544  51.6405 137.9392 0001831  75.5492  63.5011 15.49503463568399"
        self.name = "ISS (ZARYA)"
        self.satellite = EarthSatellite(self.line1, self.line2, self.name, self.ts)

    def get_current_position(self):
        now = self.ts.now()
        geocentric = self.satellite.at(now)
        subpoint = geocentric.subpoint()
        
        velocity_vector = geocentric.velocity.km_per_s
        speed_km_s = (velocity_vector[0]**2 + velocity_vector[1]**2 + velocity_vector[2]**2)**0.5
        speed_km_h = speed_km_s * 3600

        return {
            "satellite_name": self.name,
            "latitude": round(subpoint.latitude.degrees, 4),
            "longitude": round(subpoint.longitude.degrees, 4),
            "altitude_km": round(subpoint.elevation.km, 2),
            "velocity_km_h": round(speed_km_h, 2),
            "timestamp": datetime.datetime.now().isoformat()
        }

if __name__ == "__main__":
    tracker = ISSTracker()
    pos = tracker.get_current_position()
    print("\n??  ISS CURRENT POSITION")
    print("------------------------")
    print(f"Latitude : {pos['latitude']} degrees")
    print(f"Longitude: {pos['longitude']} degrees")
    print(f"Altitude : {pos['altitude_km']} km")
