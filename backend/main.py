import asyncio
import os
import sys
import sqlite3
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Ensure core app directories are in the system path
sys.path.append(os.getcwd())
from backend.services.tracking.router import router as tracking_router
from backend.services.tracking.router import tracker
from backend.services.computer_vision.optical_analyzer import OpticalIngestionEngine

# Infrastructure Instantiation
engine = OpticalIngestionEngine()
DB_PATH = os.path.join('backend', 'services', 'database', 'astronomy_history.db')

async def TLE_background_worker():
    """Manages background data updates for satellite tracking catalog."""
    while True:
        try:
            if tracker:
                if hasattr(tracker, '_ensure_data_freshness'):
                    tracker._ensure_data_freshness()
                if hasattr(tracker, 'load_catalog'):
                    tracker.load_catalog()
                    print("✓ Satellite catalog background refresh complete.")
        except Exception as e:
            print(f"⚠️ Error running background TLE refresh: {e}")
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown execution safety hooks."""
    worker_task = asyncio.create_task(TLE_background_worker())
    yield
    worker_task.cancel()

app = FastAPI(
    title="Project AstroEdge - AI Observatory Core",
    version="1.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active Route Components
app.include_router(tracking_router)

@app.get("/")
async def root_status():
    """Returns platform core subsystem operational statuses."""
    cv_val = getattr(tracker, 'cv', "NOT_INITIALIZED")
    return {
        "status": "ONLINE",
        "platform": "Project AstroEdge Core Engine",
        "version": "1.1.0",
        "satellite_tracking_cv": cv_val,
        "optical_engine": "ACTIVE"
    }

@app.get("/api/history")
async def get_analysis_history():
    """Queries logged star detection data entries for historical metric streams."""
    if not os.path.exists(DB_PATH):
        return []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM star_detection_metrics ORDER BY timestamp DESC LIMIT 100')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/analyze')
async def analyze_image(image_path: str):
    """Processes localized target frame arrays and saves metrics directly to database logs."""
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail=f"Image path not found: {image_path}")
    try:
        metrics = engine.process_image(image_path)
        
        stars_detected = metrics.get('stars_detected', 0)
        brightest_star = metrics.get('brightest_star', metrics.get('mean_brightness', 0))
        avg_area = metrics.get('average_star_area', metrics.get('std_dev', 0))
        filename = os.path.basename(image_path)
        current_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

        if os.path.exists(DB_PATH):
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                query = """
                    INSERT INTO star_detection_metrics 
                    (timestamp, image_name, stars_detected, brightest_star_pixel_value, average_star_area)
                    VALUES (?, ?, ?, ?, ?)
                """
                cursor.execute(query, (current_timestamp, filename, stars_detected, int(brightest_star), float(avg_area)))
                conn.commit()

        return {"status": "success", "data": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """Establishes real-time persistent telemetry connection tunnel for responsive interfaces."""
    await websocket.accept()
    print("📡 Dashboard connected via WebSocket telemetry layer.")
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "event": "telemetry_ping",
                "message": "AstroEdge Core Engine broadcast active"
            })
    except WebSocketDisconnect:
        print("🔌 Dashboard disconnected from WebSocket layer.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)