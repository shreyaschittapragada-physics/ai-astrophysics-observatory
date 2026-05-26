from backend.services.tracking.iss_tracker import ISSTracker

def run_test():
    tracker = ISSTracker()
    live_positions = tracker.calculate_positions()
    
    print("\n🛰️ Live Multi-Satellite Telemetry Array Matrix:")
    for name, telemetry in live_positions.items():
        print(f"   • {name:25} -> Azimuth: {telemetry['azimuth']:6}° | Elevation: {telemetry['elevation']:6}°")

if __name__ == "__main__":
    run_test()
