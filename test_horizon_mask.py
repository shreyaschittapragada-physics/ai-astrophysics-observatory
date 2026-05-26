from backend.services.tracking.horizon_mask import HorizonMaskEngine

def run_test():
    engine = HorizonMaskEngine()
    
    # Test Case A: Target to the North (0 deg Az) at a low 15 deg El. Should be blocked by the 25 deg tree line.
    case_a = engine.is_target_obstructed(azimuth=5.0, elevation=15.0)
    
    # Test Case B: Target to the South (180 deg Az) at 12 deg El. Should be clear (limit is 10 deg).
    case_b = engine.is_target_obstructed(azimuth=185.0, elevation=12.0)
    
    print("\n🔬 Testing Horizon Mask Logic Matrices:")
    print(f"   • Case A (North Anomaly @ 15° El) -> Obstructed? {case_a} (Expected: True)")
    print(f"   • Case B (South Clean Pass @ 12° El) -> Obstructed? {case_b} (Expected: False)")

if __name__ == "__main__":
    run_test()
