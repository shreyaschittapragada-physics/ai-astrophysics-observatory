import time
import io
import requests
import numpy as np
from PIL import Image

BASE_URL = "http://127.0.0.1:8000"

def test_telemetry_latencies(runs=20):
    print(f"\n--- 🛰️ PHASE 1: TARGETING CORE PERFORMANCE TESTS ({runs} Iterations) ---")
    latencies = []
    
    for i in range(runs):
        start_time = time.perf_counter()
        try:
            response = requests.get(
                f"{BASE_URL}/api/satellite/telemetry",
                params={"target": "iss", "lat": 17.385, "lon": 78.486, "alt": 542.0},
                timeout=2.0
            )
            duration = (time.perf_counter() - start_time) * 1000  # Convert to ms
            
            if response.status_code == 200:
                latencies.append(duration)
                print(f" Pulse {i+1:02d}: Success | Latency: {duration:.2f} ms")
            else:
                print(f" Pulse {i+1:02d}: Failed HTTP status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f" Pulse {i+1:02d}: Request Error -> {e}")
            
    if latencies:
        avg_lat = sum(latencies) / len(latencies)
        print(f"\n📈 BENCHMARK RESULTS:")
        print(f" 🌟 Minimum Latency : {min(latencies):.2f} ms")
        print(f" 🌟 Average Latency : {avg_lat:.2f} ms")
        print(f" 🌟 Maximum Latency : {max(latencies):.2f} ms")
    else:
        print("❌ Latency test matrix completely failed.")

def test_cv_streaming_frame():
    print("\n--- 👁️ PHASE 2: COMPUTER VISION STREAMING INGESTION TEST ---")
    
    # 1. Create a mock synthetic star-field image frame entirely in memory
    print(" Mocking a 512x512 monochrome stellar image...")
    img_array = np.zeros((512, 512), dtype=np.uint8)
    
    # Inject a few high-brightness mock stellar centroids (stars)
    img_array[120, 150] = 255  # Star Alpha
    img_array[340, 410] = 240  # Star Beta
    img_array[200, 210] = 200  # Star Gamma
    
    # 2. Convert raw NumPy matrix into an HTTP-uploadable binary data stream
    img = Image.fromarray(img_array)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    # 3. Stream raw payload directly into the FastAPI endpoint
    print(" Streaming binary frame payload to /api/cv/streaming-frame...")
    try:
        files = {'file': ('mock_starframe.png', img_byte_arr, 'image/png')}
        start_time = time.perf_counter()
        response = requests.post(f"{BASE_URL}/api/cv/streaming-frame", files=files, timeout=5.0)
        duration = (time.perf_counter() - start_time) * 1000
        
        print(f" Server Processing Handshake Response Time: {duration:.2f} ms")
        print(f" Response Status Code: {response.status_code}")
        print(" Payload Extracted Return Matrix:")
        print(response.json())
        
    except requests.exceptions.RequestException as e:
        print(f"❌ CV Streaming Pipeline Failed -> {e}")

if __name__ == "__main__":
    print("==========================================================")
    print("🛸 v1.1-TRACKING-CORE : AUTOMATED SPRINT 3 PERFORMANCE SUITE")
    print("==========================================================")
    test_telemetry_latencies(runs=15)
    test_cv_streaming_frame()
