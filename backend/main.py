from fastapi import FastAPI, Query, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import datetime
import sqlite3
import numpy as np
from PIL import Image
import io

# Aligned with your exact VS Code Explorer paths
from backend.services.tracking.iss_tracker import ISSTracker
from backend.services.computer_vision import star_detection

app = FastAPI(title="AI Astrophysics Core Engine - V1.1-Tracking-Core", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "astronomy_history.db"
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracking_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            satellite TEXT,
            azimuth REAL,
            elevation REAL,
            range_km REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

try:
    tracker = ISSTracker()
    if hasattr(star_detection, "StarDetector"):
        detector = star_detection.StarDetector(sigma_threshold=3.0)
    elif hasattr(star_detection, "StarDetection"):
        detector = star_detection.StarDetection(sigma_threshold=3.0)
    else:
        detector = star_detection
except Exception:
    tracker = None
    detector = None

@app.get("/api/satellite/telemetry")
def get_telemetry(
    target: str = Query("iss"),
    lat: float = Query(17.385),
    lon: float = Query(78.486),
    alt: float = Query(542.0)
):
    if not tracker:
        raise HTTPException(status_code=503, detail="Tracking engine offline")
    try:
        pos = tracker.get_current_position(target)
        angles = tracker.get_look_angles(target, lat, lon, alt)
        
        # FIX: Clean and explicitly typecast NumPy types to standard Python primitives
        clean_telemetry = {
            "latitude": float(pos.get("latitude", 0.0)),
            "longitude": float(pos.get("longitude", 0.0)),
            "altitude_km": float(pos.get("altitude_km", 0.0)),
            "velocity_km_h": float(pos.get("velocity_km_h", 0.0)),
            "azimuth_deg": float(angles.get("azimuth_deg", 0.0)),
            "elevation_deg": float(angles.get("elevation_deg", 0.0)),
            "range_km": float(angles.get("range_km", 0.0)),
            "is_above_horizon": bool(angles.get("is_above_horizon", False)),
            "engine_status": "OPERATIONAL",
            "last_pulse": datetime.datetime.now().strftime("%H:%M:%S")
        }
        
        # Log to local history SQLite cache
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tracking_history (timestamp, satellite, azimuth, elevation, range_km) VALUES (?, ?, ?, ?, ?)",
            (datetime.datetime.now().isoformat(), target, clean_telemetry["azimuth_deg"], clean_telemetry["elevation_deg"], clean_telemetry["range_km"])
        )
        conn.commit()
        conn.close()
        
        return clean_telemetry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/satellite/passes")
def get_passes(
    target: str = Query("iss"),
    lat: float = Query(17.385),
    lon: float = Query(78.486),
    alt: float = Query(542.0)
):
    if not tracker:
        return []
    try:
        raw_passes = tracker.compute_future_passes(target, lat, lon, alt, days=7)
        return [{
            "rise": p["rise_time"].split("T")[1][:8] + " UTC",
            "set": p["set_time"].split("T")[1][:8] + " UTC",
            "max_el": float(p["max_elevation_deg"]),
            "azimuth": float(p["peak_azimuth_deg"]),
            "visible": "HIGHLY VISIBLE" if p["max_elevation_deg"] > 40 else "LOW VISIBILITY"
        } for p in raw_passes]
    except Exception:
        return []

@app.post("/api/cv/streaming-frame")
async def analyze_streaming_frame(file: UploadFile = File(...)):
    if not detector:
        raise HTTPException(status_code=503, detail="CV Engine offline")
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("L")
        img_array = np.array(image)
        
        if hasattr(detector, "process_feed"):
            return detector.process_feed(img_array)
        elif hasattr(detector, "process_image"):
            return detector.process_image(img_array)
        else:
            raise HTTPException(status_code=500, detail="Star detection process target function missing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>🛰️ V1 Tracking Core Console</title>
        <style>
            body { background: #0b0f19; color: #c3cbdb; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-top: 20px; }
            .card { background: #141b2d; border: 1px solid #1f2a40; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
            h1 { color: #4cceac; font-size: 24px; margin: 0; }
            h2 { color: #868dfb; font-size: 12px; text-transform: uppercase; margin-bottom: 15px; letter-spacing: 1px; }
            .metric { font-size: 28px; font-weight: bold; color: white; }
            .unit { font-size: 14px; color: #a3aed0; }
            input, select { background: #1f2a40; color: white; border: 1px solid #4cceac; padding: 8px; border-radius: 4px; width: 100%; box-sizing: border-box; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #1f2a40; }
            th { color: #868dfb; font-size: 11px; }
            .horizon-true { color: #4cceac; font-weight: bold; }
            .horizon-false { color: #f44336; font-weight: bold; }
        </style>
    </head>
    <body>
        <div style="max-width: 1200px; margin: 0 auto;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <div>
                    <h1>ASTROPHYSICS OBSERVATORY DESK</h1>
                    <div style="font-size:12px; color:#a3aed0;">MILESTONE: v1.1-tracking-core</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 14px; color: white;">ENGINE: <strong id="engine-status" style="color:#4cceac;">ACTIVE</strong></div>
                    <div style="font-size: 11px; color:#a3aed0;">PULSE: <span id="last-pulse">--</span></div>
                </div>
            </div>

            <div class="card">
                <h2>🛰️ Target Vector Parameters</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <div>
                        <label style="font-size:11px; color:#a3aed0;">SELECT SATELLITE CORE</label>
                        <select id="sat-target" onchange="runGlobalUpdate()">
                            <option value="iss">International Space Station (ISS)</option>
                            <option value="tiangong">Tiangong Space Station (CSS)</option>
                            <option value="hubble">Hubble Space Telescope (HST)</option>
                        </select>
                    </div>
                    <div>
                        <label style="font-size:11px; color:#a3aed0;">OBSERVER LATITUDE</label>
                        <input type="number" id="obs-lat" value="17.385" step="0.001" onchange="runGlobalUpdate()">
                    </div>
                    <div>
                        <label style="font-size:11px; color:#a3aed0;">OBSERVER LONGITUDE</label>
                        <input type="number" id="obs-lon" value="78.486" step="0.001" onchange="runGlobalUpdate()">
                    </div>
                </div>
            </div>

            <div class="grid">
                <div class="card"><h2>Subpoint Latitude</h2><div class="metric" id="sat-lat">0.0000 <span class="unit">°</span></div></div>
                <div class="card"><h2>Subpoint Longitude</h2><div class="metric" id="sat-lon">0.0000 <span class="unit">°</span></div></div>
                <div class="card"><h2>Orbital Altitude</h2><div class="metric" id="sat-alt">0.00 <span class="unit">km</span></div></div>
                <div class="card"><h2>Velocity</h2><div class="metric" id="sat-vel">0.00 <span class="unit">km/h</span></div></div>
                <div class="card"><h2>Local Elevation</h2><div class="metric" id="sat-elevation">0.00 <span class="unit">°</span></div></div>
                <div class="card"><h2>Local Azimuth</h2><div class="metric" id="sat-azimuth">0.00 <span class="unit">°</span></div></div>
                <div class="card"><h2>Observer Range</h2><div class="metric" id="sat-range">0.00 <span class="unit">km</span></div></div>
                <div class="card"><h2>Horizon Status</h2><div class="metric" id="sat-horizon">N/A</div></div>
            </div>

            <div class="card" style="margin-top:20px;">
                <h2>🔮 Operational Overflight Pass Matrix (Next 7 Days)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>AOS (Rise Time)</th>
                            <th>Max Elevation</th>
                            <th>Peak Azimuth Heading</th>
                            <th>LOS (Set Time)</th>
                            <th>Optical Visibility Evaluation</th>
                        </tr>
                    </thead>
                    <tbody id="pass-table-body">
                        <tr><td colspan="5" style="color:#a3aed0;">Computing future horizon crossings...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <script>
            async function fetchTelemetry() {
                const target = document.getElementById('sat-target').value;
                const lat = document.getElementById('obs-lat').value;
                const lon = document.getElementById('obs-lon').value;
                try {
                    const response = await fetch(`/api/satellite/telemetry?target=${target}&lat=${lat}&lon=${lon}&alt=542.0`);
                    const data = await response.json();
                    if(response.ok) {
                        document.getElementById('sat-lat').innerHTML = `${data.latitude.toFixed(4)} <span class="unit">°</span>`;
                        document.getElementById('sat-lon').innerHTML = `${data.longitude.toFixed(4)} <span class="unit">°</span>`;
                        document.getElementById('sat-alt').innerHTML = `${data.altitude_km.toFixed(2)} <span class="unit">km</span>`;
                        document.getElementById('sat-vel').innerHTML = `${Number(data.velocity_km_h.toFixed(0)).toLocaleString()} <span class="unit">km/h</span>`;
                        document.getElementById('sat-elevation').innerHTML = `${data.elevation_deg.toFixed(2)} <span class="unit">°</span>`;
                        document.getElementById('sat-azimuth').innerHTML = `${data.azimuth_deg.toFixed(2)} <span class="unit">°</span>`;
                        document.getElementById('sat-range').innerHTML = `${Number(data.range_km.toFixed(0)).toLocaleString()} <span class="unit">km</span>`;
                        
                        const horizonEl = document.getElementById('sat-horizon');
                        if(data.is_above_horizon) {
                            horizonEl.innerHTML = '<span class="horizon-true">VISIBLE ABOVE HORIZON</span>';
                        } else {
                            horizonEl.innerHTML = '<span class="horizon-false">BELOW HORIZON</span>';
                        }
                        document.getElementById('last-pulse').innerText = data.last_pulse;
                    }
                } catch (error) {}
            }

            async function fetchPasses() {
                const target = document.getElementById('sat-target').value;
                const lat = document.getElementById('obs-lat').value;
                const lon = document.getElementById('obs-lon').value;
                try {
                    const response = await fetch(`/api/satellite/passes?target=${target}&lat=${lat}&lon=${lon}&alt=542.0`);
                    const data = await response.json();
                    const tbody = document.getElementById('pass-table-body');
                    if(response.ok && data.length > 0) {
                        tbody.innerHTML = "";
                        data.forEach(p => {
                            const cl = p.visible === "HIGHLY VISIBLE" ? "color:#4cceac;font-weight:bold;" : "color:#ffb74d;";
                            tbody.innerHTML += `<tr><td><strong>${p.rise}</strong></td><td>${p.max_el.toFixed(1)}°</td><td>${p.azimuth.toFixed(1)}°</td><td>${p.set}</td><td><span style="${cl}">${p.visible}</span></td></tr>`;
                        });
                    }
                } catch(e) {}
            }

            function runGlobalUpdate() { fetchTelemetry(); fetchPasses(); }
            setInterval(fetchTelemetry, 1000);
            setInterval(fetchPasses, 60000);
            window.onload = runGlobalUpdate;
        </script>
    </body>
    </html>
    """
